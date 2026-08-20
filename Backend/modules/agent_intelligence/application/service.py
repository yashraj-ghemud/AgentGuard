"""
Agent Intelligence Service

Business logic for analyzing agent capabilities using LLM.
"""
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.orm import Session

from modules.agent_intelligence.domain.models import AgentCapabilityProfile
from modules.agent_intelligence.domain.schemas import (
    AgentCapabilityAnalysis,
    AgentCapabilityProfileResponse,
)
from modules.agent_intelligence.infrastructure.repository import AgentIntelligenceRepository
from modules.agent_registry.infrastructure.repository import AgentRepository
from modules.tool_registry.infrastructure.repository import ToolRepository
from core.llm import get_llm_provider, get_llm_settings
from core.events.base import IEventPublisher
from core.events.domain_events import DomainEvent
from shared.exceptions import NotFoundError, InternalError
from shared.utils import utc_now

# Generator version for tracking analysis changes
GENERATOR_VERSION = "1.0.0"


class AgentAnalysisStarted(DomainEvent):
    """Event: Agent analysis started."""
    event_type: str = "agent_intelligence.analysis_started"
    agent_id: UUID
    version_id: Optional[UUID] = None


class AgentAnalysisCompleted(DomainEvent):
    """Event: Agent analysis completed."""
    event_type: str = "agent_intelligence.analysis_completed"
    agent_id: UUID
    capability_profile_id: UUID


class AgentAnalysisFailed(DomainEvent):
    """Event: Agent analysis failed."""
    event_type: str = "agent_intelligence.analysis_failed"
    agent_id: UUID
    error_message: str


class AgentIntelligenceService:
    """Service for analyzing agent capabilities."""

    def __init__(
        self,
        db: Session,
        event_publisher: Optional[IEventPublisher] = None
    ):
        """
        Initialize service.
        
        Args:
            db: Database session
            event_publisher: Optional event publisher
        """
        self.db = db
        self.repository = AgentIntelligenceRepository(db)
        self.agent_repo = AgentRepository(db)
        self.tool_repo = ToolRepository(db)
        self.event_publisher = event_publisher
        self.llm = get_llm_provider()
        self.settings = get_llm_settings()

    async def analyze_agent(
        self,
        agent_id: UUID,
        version_id: Optional[UUID] = None,
        force_regenerate: bool = False,
        custom_constraints: Optional[List[str]] = None
    ) -> AgentCapabilityProfile:
        """
        Analyze an agent to generate capability profile.
        
        Args:
            agent_id: Agent ID
            version_id: Optional specific version
            force_regenerate: Force new analysis even if cached
            custom_constraints: Additional constraints to consider
            
        Returns:
            Agent capability profile
            
        Raises:
            NotFoundError: If agent not found
            InternalError: If analysis fails
        """
        # Publish start event
        if self.event_publisher:
            await self.event_publisher.publish(
                AgentAnalysisStarted(agent_id=agent_id, version_id=version_id)
            )
        
        try:
            # Check for existing profile
            if not force_regenerate:
                existing = self.repository.get_by_agent(agent_id, version_id)
                if existing:
                    return existing
            
            # Get agent data
            agent = self.agent_repo.get_by_id(agent_id)
            if not agent:
                raise NotFoundError("Agent", str(agent_id))
            
            # Get tools
            tools = self.tool_repo.list_by_agent(agent_id)
            
            # Generate analysis using LLM
            analysis = await self._generate_analysis(
                agent=agent,
                tools=tools,
                custom_constraints=custom_constraints
            )
            
            # Create profile
            profile = self._create_profile_from_analysis(
                agent_id=agent_id,
                version_id=version_id,
                analysis=analysis
            )
            
            # Save
            profile = self.repository.create(profile)
            self.db.commit()
            
            # Publish completion event
            if self.event_publisher:
                await self.event_publisher.publish(
                    AgentAnalysisCompleted(
                        agent_id=agent_id,
                        capability_profile_id=profile.id
                    )
                )
            
            return profile
            
        except Exception as e:
            self.db.rollback()
            
            # Publish failure event
            if self.event_publisher:
                await self.event_publisher.publish(
                    AgentAnalysisFailed(
                        agent_id=agent_id,
                        error_message=str(e)
                    )
                )
            
            if isinstance(e, NotFoundError):
                raise
            raise InternalError(f"Agent analysis failed: {str(e)}")

    async def _generate_analysis(
        self,
        agent,
        tools: List,
        custom_constraints: Optional[List[str]] = None
    ) -> AgentCapabilityAnalysis:
        """
        Generate capability analysis using LLM.
        
        Args:
            agent: Agent model
            tools: List of tool models
            custom_constraints: Additional constraints
            
        Returns:
            Structured analysis
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(agent, tools, custom_constraints)
        
        # Call LLM with structured output
        analysis = await self.llm.generate_structured(
            prompt=prompt,
            schema=AgentCapabilityAnalysis,
            model=self.settings.agent_analysis_model,
            temperature=self.settings.agent_analysis_temperature,
            max_tokens=self.settings.max_tokens_per_request,
            system_prompt=self._get_system_prompt()
        )
        
        return analysis

    def _build_analysis_prompt(
        self,
        agent,
        tools: List,
        custom_constraints: Optional[List[str]] = None
    ) -> str:
        """Build prompt for agent analysis."""
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(
                f"- {tool.name} (risk: {tool.risk_level}): "
                f"{'Destructive' if tool.is_destructive else 'Non-destructive'}, "
                f"{'Reversible' if tool.is_reversible else 'Irreversible'}, "
                f"{'Requires confirmation' if tool.requires_confirmation else 'No confirmation'}"
            )
        
        tools_text = "\n".join(tool_descriptions) if tool_descriptions else "No tools registered yet."
        
        constraints_text = ""
        if custom_constraints:
            constraints_text = "\n\nAdditional Constraints:\n" + "\n".join(f"- {c}" for c in custom_constraints)
        
        prompt = f"""Analyze this AI agent to understand its capabilities, risks, and potential failure points.

Agent Information:
- Name: {agent.name}
- Execution Mode: {agent.execution_mode}
- Status: {agent.status}
- Description: {agent.agent_metadata.get('description', 'Not provided')}
- Tags: {', '.join(agent.agent_metadata.get('tags', []))}

Registered Tools:
{tools_text}

Risk Profile Configuration:
{agent.risk_profile if agent.risk_profile else 'No risk profile configured'}
{constraints_text}

Your task:
1. Identify the agent's primary goal and any secondary goals
2. List specific capabilities this agent has
3. Identify domains this agent operates in (e.g., customer support, travel, coding, finance)
4. For each tool, explain what capability it provides
5. Identify high-risk and destructive operations
6. List required and optional user inputs
7. Identify ambiguity points where user input might be unclear
8. Identify potential failure surfaces (where the agent might fail)
9. Identify security surfaces (where malicious actors might attack)
10. List assumptions the agent makes
11. List constraints the agent should follow

Provide your analysis in the structured format specified."""
        
        return prompt

    def _get_system_prompt(self) -> str:
        """Get system prompt for analysis."""
        return """You are an AI agent analyzer. Your job is to deeply understand what an AI agent is designed to do, what it's capable of, where it might fail, and where it might be vulnerable.

Focus on:
- Understanding the agent's PURPOSE (what problem it solves)
- Identifying CAPABILITIES (what it can do)
- Assessing RISKS (what could go wrong)
- Finding AMBIGUITIES (where users might be unclear)
- Spotting FAILURES (where the agent might fail)
- Detecting SECURITY ISSUES (where attacks might occur)

Be specific and concrete. Avoid generic statements.
For each capability, tool, risk, or failure point, explain WHY it matters.

Your analysis will be used to generate targeted test scenarios."""

    def _create_profile_from_analysis(
        self,
        agent_id: UUID,
        version_id: Optional[UUID],
        analysis: AgentCapabilityAnalysis
    ) -> AgentCapabilityProfile:
        """Create database model from analysis."""
        return AgentCapabilityProfile(
            agent_id=agent_id,
            version_id=version_id,
            primary_goal=analysis.primary_goal,
            secondary_goals=[g for g in analysis.secondary_goals],
            capabilities=[c.model_dump() for c in analysis.capabilities],
            domains=analysis.domains,
            tool_capabilities=[tc.model_dump() for tc in analysis.tool_capabilities],
            high_risk_operations=[op.model_dump() for op in analysis.high_risk_operations],
            destructive_operations=[op.model_dump() for op in analysis.destructive_operations],
            reversible_operations=[op.model_dump() for op in analysis.reversible_operations],
            required_inputs=analysis.required_inputs,
            optional_inputs=analysis.optional_inputs,
            ambiguity_points=[ap.model_dump() for ap in analysis.ambiguity_points],
            failure_surfaces=[fs.model_dump() for fs in analysis.failure_surfaces],
            security_surfaces=[ss.model_dump() for ss in analysis.security_surfaces],
            assumptions=analysis.assumptions,
            constraints=analysis.constraints,
            confidence=analysis.confidence.model_dump(),
            model_used=self.settings.agent_analysis_model,
            generator_version=GENERATOR_VERSION,
            generation_timestamp=utc_now(),
        )

    def get_profile(
        self,
        agent_id: UUID,
        version_id: Optional[UUID] = None
    ) -> Optional[AgentCapabilityProfile]:
        """
        Get existing capability profile.
        
        Args:
            agent_id: Agent ID
            version_id: Optional version ID
            
        Returns:
            Profile if exists
        """
        return self.repository.get_by_agent(agent_id, version_id)

    def get_profile_by_id(self, profile_id: UUID) -> Optional[AgentCapabilityProfile]:
        """Get profile by ID."""
        return self.repository.get_by_id(profile_id)

    def list_profiles(self, agent_id: UUID, limit: int = 10) -> List[AgentCapabilityProfile]:
        """List all profiles for an agent."""
        return self.repository.list_by_agent(agent_id, limit)

    def to_response(self, profile: AgentCapabilityProfile) -> AgentCapabilityProfileResponse:
        """Convert model to API response."""
        return AgentCapabilityProfileResponse.model_validate(profile)
