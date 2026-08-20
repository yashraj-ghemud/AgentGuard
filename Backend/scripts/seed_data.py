"""
Seed database with demo data for development.

Usage:
    python scripts/seed_data.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database.base import get_engine, Base
from core.config.settings import get_settings
from modules.agent_registry.domain.models import Agent
from modules.agent_versioning.domain.models import AgentVersion
from modules.tool_registry.domain.models import Tool
from shared.types import EntityStatus, RiskLevel
from shared.utils import generate_id, utc_now


def seed_database():
    """Seed database with demo data."""
    settings = get_settings()
    engine = get_engine()
    
    # Create tables if they don't exist
    Base.metadata.create_all(engine)
    
    with Session(engine) as session:
        print("🌱 Seeding database...")
        
        # Create demo workspace
        demo_workspace_id = generate_id()
        
        # ==================================================================
        # Agent 1: Customer Support Agent
        # ==================================================================
        print("\n📦 Creating Customer Support Agent...")
        agent1_id = generate_id()
        agent1 = Agent(
            id=agent1_id,
            name="Customer Support Agent",
            description="AI agent that handles customer support inquiries, order tracking, and basic troubleshooting",
            endpoint_url="https://example.com/api/agents/customer-support",
            execution_mode="http",
            purpose="Provide 24/7 customer support for e-commerce platform",
            status=EntityStatus.ACTIVE,
            risk_profile={
                "risk_level": "medium",
                "requires_human_approval": False,
                "max_execution_time_seconds": 120,
                "allowed_failure_rate": 0.05
            },
            agent_metadata={
                "department": "customer_service",
                "model": "gpt-4",
                "region": "us-east-1"
            },
            workspace_id=demo_workspace_id,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(agent1)
        
        # Tools for Customer Support Agent
        tool1 = Tool(
            id=generate_id(),
            agent_id=agent1_id,
            name="search_order",
            description="Search for customer orders by order number or email address",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Order number or email"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10}
                },
                "required": ["query"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "orders": {"type": "array", "items": {"type": "object"}},
                    "total": {"type": "integer"}
                }
            },
            risk_level=RiskLevel.LOW.value,
            is_destructive=False,
            is_reversible=True,
            requires_confirmation=False,
            timeout_seconds=30,
            status=EntityStatus.ACTIVE.value,
            tool_metadata={"category": "data_access"},
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(tool1)
        
        tool2 = Tool(
            id=generate_id(),
            agent_id=agent1_id,
            name="cancel_order",
            description="Cancel a customer order if it hasn't been shipped yet",
            input_schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "Order ID to cancel"},
                    "reason": {"type": "string", "description": "Cancellation reason"}
                },
                "required": ["order_id", "reason"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "refund_amount": {"type": "number"},
                    "refund_status": {"type": "string"}
                }
            },
            risk_level=RiskLevel.HIGH.value,
            is_destructive=True,
            is_reversible=False,
            requires_confirmation=True,
            timeout_seconds=60,
            status=EntityStatus.ACTIVE.value,
            tool_metadata={"category": "order_management"},
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(tool2)
        
        # Version 1 of Customer Support Agent
        version1 = AgentVersion(
            id=generate_id(),
            agent_id=agent1_id,
            version_number="v1",
            snapshot={
                "agent_id": str(agent1_id),
                "name": agent1.name,
                "description": agent1.description,
                "endpoint_url": agent1.endpoint_url,
                "execution_mode": agent1.execution_mode,
                "purpose": agent1.purpose,
                "status": agent1.status.value,
                "risk_profile": agent1.risk_profile,
                "metadata": agent1.agent_metadata,
                "workspace_id": str(demo_workspace_id) if demo_workspace_id else None,
                "captured_at": utc_now().isoformat(),
                "tool_ids": []
            },
            notes="Initial version - basic customer support capabilities",
            snapshot_metadata={"deployment": "production", "release_date": "2024-01-15"},
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(version1)
        
        # ==================================================================
        # Agent 2: Content Moderation Agent
        # ==================================================================
        print("📦 Creating Content Moderation Agent...")
        agent2_id = generate_id()
        agent2 = Agent(
            id=agent2_id,
            name="Content Moderation Agent",
            description="AI agent that reviews user-generated content for policy violations",
            endpoint_url="https://example.com/api/agents/content-moderation",
            execution_mode="http",
            purpose="Automatically moderate user content to maintain community standards",
            status=EntityStatus.ACTIVE,
            risk_profile={
                "risk_level": "critical",
                "requires_human_approval": True,
                "max_execution_time_seconds": 30,
                "allowed_failure_rate": 0.01
            },
            agent_metadata={
                "department": "trust_and_safety",
                "model": "gpt-4",
                "region": "global"
            },
            workspace_id=demo_workspace_id,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(agent2)
        
        # Tools for Content Moderation Agent
        tool3 = Tool(
            id=generate_id(),
            agent_id=agent2_id,
            name="analyze_content",
            description="Analyze content for policy violations (hate speech, violence, spam, etc.)",
            input_schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string", "description": "Content to analyze"},
                    "content_type": {"type": "string", "enum": ["text", "image", "video"]},
                    "user_id": {"type": "string"}
                },
                "required": ["content", "content_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "violations": {"type": "array", "items": {"type": "string"}},
                    "severity": {"type": "string", "enum": ["none", "low", "medium", "high", "critical"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "recommended_action": {"type": "string"}
                }
            },
            risk_level=RiskLevel.MEDIUM.value,
            is_destructive=False,
            is_reversible=True,
            requires_confirmation=False,
            timeout_seconds=30,
            status=EntityStatus.ACTIVE.value,
            tool_metadata={"category": "analysis"},
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(tool3)
        
        tool4 = Tool(
            id=generate_id(),
            agent_id=agent2_id,
            name="remove_content",
            description="Remove content that violates community guidelines",
            input_schema={
                "type": "object",
                "properties": {
                    "content_id": {"type": "string", "description": "ID of content to remove"},
                    "violation_type": {"type": "string"},
                    "notify_user": {"type": "boolean", "default": True}
                },
                "required": ["content_id", "violation_type"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "content_archived": {"type": "boolean"},
                    "user_notified": {"type": "boolean"}
                }
            },
            risk_level=RiskLevel.CRITICAL.value,
            is_destructive=True,
            is_reversible=True,
            requires_confirmation=True,
            timeout_seconds=60,
            status=EntityStatus.ACTIVE.value,
            tool_metadata={"category": "content_management"},
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(tool4)
        
        # ==================================================================
        # Agent 3: Data Analysis Agent (Inactive)
        # ==================================================================
        print("📦 Creating Data Analysis Agent (inactive)...")
        agent3_id = generate_id()
        agent3 = Agent(
            id=agent3_id,
            name="Data Analysis Agent",
            description="AI agent that performs statistical analysis and generates insights from business data",
            endpoint_url="https://example.com/api/agents/data-analysis",
            execution_mode="sdk",
            purpose="Provide automated data analysis and business intelligence",
            status=EntityStatus.INACTIVE,
            risk_profile={
                "risk_level": "low",
                "requires_human_approval": False,
                "max_execution_time_seconds": 300,
                "allowed_failure_rate": 0.1
            },
            agent_metadata={
                "department": "analytics",
                "model": "gpt-3.5-turbo",
                "region": "us-west-2",
                "note": "Currently being updated to new model"
            },
            workspace_id=demo_workspace_id,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(agent3)
        
        # Commit all changes
        session.commit()
        
        print("\n✅ Database seeded successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Workspace ID: {demo_workspace_id}")
        print(f"   - Agents created: 3")
        print(f"   - Tools created: 4")
        print(f"   - Versions created: 1")
        print(f"\n🔗 Try the API:")
        print(f"   - GET http://localhost:8000/api/v1/agents")
        print(f"   - GET http://localhost:8000/api/v1/agents/{agent1_id}")
        print(f"   - GET http://localhost:8000/api/v1/agents/{agent1_id}/tools")
        print(f"   - GET http://localhost:8000/api/v1/agents/{agent1_id}/versions")
        print(f"\n📚 API Docs: http://localhost:8000/docs")


if __name__ == "__main__":
    try:
        seed_database()
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
