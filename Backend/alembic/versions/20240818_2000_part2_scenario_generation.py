"""Part 2: Scenario Generation tables

Revision ID: 20240818_2000
Revises: 001_initial
Create Date: 2024-08-18 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20240818_2000'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create Part 2 tables for scenario generation."""
    
    # ========================================================================
    # Table: agent_capability_profiles
    # ========================================================================
    op.create_table(
        'agent_capability_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Core understanding
        sa.Column('primary_goal', sa.Text, nullable=True),
        sa.Column('secondary_goals', postgresql.JSONB, nullable=False, server_default='[]'),
        
        # Capabilities
        sa.Column('capabilities', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('domains', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('tool_capabilities', postgresql.JSONB, nullable=False, server_default='[]'),
        
        # Risk and operations
        sa.Column('high_risk_operations', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('destructive_operations', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('reversible_operations', postgresql.JSONB, nullable=False, server_default='[]'),
        
        # Inputs
        sa.Column('required_inputs', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('optional_inputs', postgresql.JSONB, nullable=False, server_default='[]'),
        
        # Failure surfaces
        sa.Column('ambiguity_points', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('failure_surfaces', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('security_surfaces', postgresql.JSONB, nullable=False, server_default='[]'),
        
        # Constraints
        sa.Column('assumptions', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('constraints', postgresql.JSONB, nullable=False, server_default='[]'),
        
        # Quality metadata
        sa.Column('confidence', postgresql.JSONB, nullable=False, server_default='{}'),
        
        # Generation metadata
        sa.Column('model_used', sa.String(100), nullable=False),
        sa.Column('generator_version', sa.String(50), nullable=False),
        sa.Column('generation_timestamp', sa.DateTime, nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['version_id'], ['agent_versions.id'], ondelete='SET NULL'),
        
        # Constraints
        sa.UniqueConstraint('agent_id', 'version_id', name='uq_capability_agent_version'),
    )
    
    # Indexes
    op.create_index('idx_capability_agent', 'agent_capability_profiles', ['agent_id'])
    op.create_index('idx_capability_version', 'agent_capability_profiles', ['version_id'])
    
    # ========================================================================
    # Table: risk_profiles
    # ========================================================================
    op.create_table(
        'risk_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('capability_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Risk assessment
        sa.Column('overall_risk', sa.String(20), nullable=False),
        sa.Column('high_risk_tools', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('critical_tools', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('unsafe_operations', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('confirmation_required_operations', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('risk_inconsistencies', postgresql.JSONB, nullable=False, server_default='[]'),
        
        # Test recommendations
        sa.Column('recommended_test_intensity', sa.String(20), nullable=False),
        sa.Column('recommended_scenario_count', sa.Integer, nullable=False),
        sa.Column('priority_test_areas', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('risk_scores', postgresql.JSONB, nullable=False, server_default='{}'),
        
        # Generation metadata
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('generator_version', sa.String(50), nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['capability_profile_id'], ['agent_capability_profiles.id'], ondelete='CASCADE'),
        
        # Constraints
        sa.UniqueConstraint('agent_id', 'capability_profile_id', name='uq_risk_agent_capability'),
    )
    
    # Indexes
    op.create_index('idx_risk_agent', 'risk_profiles', ['agent_id'])
    op.create_index('idx_risk_capability', 'risk_profiles', ['capability_profile_id'])
    
    # ========================================================================
    # Table: test_strategies
    # ========================================================================
    op.create_table(
        'test_strategies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('capability_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('risk_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Strategy configuration
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('category_distribution', postgresql.JSONB, nullable=False),
        sa.Column('total_scenario_count', sa.Integer, nullable=False),
        sa.Column('multi_turn_percentage', sa.Integer, nullable=False),
        
        # Coverage targets
        sa.Column('tool_coverage_targets', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('risk_coverage_targets', postgresql.JSONB, nullable=False, server_default='{}'),
        
        # Generation metadata
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('generator_version', sa.String(50), nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['capability_profile_id'], ['agent_capability_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['risk_profile_id'], ['risk_profiles.id'], ondelete='CASCADE'),
    )
    
    # Indexes
    op.create_index('idx_strategy_agent', 'test_strategies', ['agent_id'])
    
    # ========================================================================
    # Table: scenario_suites
    # ========================================================================
    op.create_table(
        'scenario_suites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('test_strategy_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Suite metadata
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('suite_type', sa.String(50), nullable=False),
        
        # Statistics
        sa.Column('total_scenarios', sa.Integer, nullable=False, server_default='0'),
        sa.Column('category_counts', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('priority_counts', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('risk_counts', postgresql.JSONB, nullable=False, server_default='{}'),
        
        # Coverage
        sa.Column('tool_coverage', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('coverage_score', sa.Float, nullable=True),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('generation_started_at', sa.DateTime, nullable=True),
        sa.Column('generation_completed_at', sa.DateTime, nullable=True),
        sa.Column('generation_error', sa.Text, nullable=True),
        
        # Immutability
        sa.Column('is_locked', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('locked_at', sa.DateTime, nullable=True),
        
        # Metadata
        sa.Column('generator_version', sa.String(50), nullable=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_version_id'], ['agent_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['test_strategy_id'], ['test_strategies.id'], ondelete='SET NULL'),
    )
    
    # Indexes
    op.create_index('idx_suite_agent', 'scenario_suites', ['agent_id'])
    op.create_index('idx_suite_agent_version', 'scenario_suites', ['agent_version_id'])
    op.create_index('idx_suite_status', 'scenario_suites', ['status'])
    op.create_index('idx_suite_type', 'scenario_suites', ['suite_type'])
    
    # ========================================================================
    # Table: scenarios
    # ========================================================================
    op.create_table(
        'scenarios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('scenario_suite_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_version_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        # Classification
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('subtype', sa.String(100), nullable=True),
        
        # Content
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('difficulty', sa.String(20), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        
        # Scenario data
        sa.Column('user_input', sa.Text, nullable=False),
        sa.Column('conversation_steps', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('preconditions', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('environment_requirements', postgresql.JSONB, nullable=False, server_default='{}'),
        
        # Expected behavior
        sa.Column('expected_behavior', postgresql.JSONB, nullable=False),
        sa.Column('validation_rules', postgresql.JSONB, nullable=False),
        
        # Targeting
        sa.Column('target_tools', postgresql.JSONB, nullable=False, server_default='[]'),
        sa.Column('tags', postgresql.JSONB, nullable=False, server_default='[]'),
        
        # Quality metadata
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('relevance_score', sa.Float, nullable=True),
        sa.Column('is_duplicate', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('duplicate_of_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Generation metadata
        sa.Column('generated_by', sa.String(100), nullable=False),
        sa.Column('generator_version', sa.String(50), nullable=False),
        sa.Column('generation_run_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model_used', sa.String(100), nullable=False),
        
        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('rejection_reason', sa.Text, nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['scenario_suite_id'], ['scenario_suites.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_version_id'], ['agent_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['duplicate_of_id'], ['scenarios.id'], ondelete='SET NULL'),
    )
    
    # Indexes
    op.create_index('idx_scenario_suite', 'scenarios', ['scenario_suite_id'])
    op.create_index('idx_scenario_agent_version', 'scenarios', ['agent_version_id'])
    op.create_index('idx_scenario_category', 'scenarios', ['category'])
    op.create_index('idx_scenario_priority', 'scenarios', ['priority'])
    op.create_index('idx_scenario_risk_level', 'scenarios', ['risk_level'])
    op.create_index('idx_scenario_status', 'scenarios', ['status'])
    op.create_index('idx_scenario_generation_run', 'scenarios', ['generation_run_id'])
    
    # ========================================================================
    # Table: scenario_generation_runs
    # ========================================================================
    op.create_table(
        'scenario_generation_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scenario_suite_id', postgresql.UUID(as_uuid=True), nullable=True),
        
        # Configuration
        sa.Column('requested_count', sa.Integer, nullable=False),
        sa.Column('strategy_config', postgresql.JSONB, nullable=False),
        
        # Progress
        sa.Column('status', sa.String(30), nullable=False, server_default='queued'),
        sa.Column('current_phase', sa.String(50), nullable=True),
        sa.Column('scenarios_generated', sa.Integer, nullable=False, server_default='0'),
        sa.Column('scenarios_validated', sa.Integer, nullable=False, server_default='0'),
        sa.Column('scenarios_rejected', sa.Integer, nullable=False, server_default='0'),
        
        # Timing
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('duration_seconds', sa.Float, nullable=True),
        
        # Results
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('error_details', postgresql.JSONB, nullable=True),
        
        # Resource tracking
        sa.Column('total_llm_calls', sa.Integer, nullable=False, server_default='0'),
        sa.Column('estimated_cost', sa.Float, nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scenario_suite_id'], ['scenario_suites.id'], ondelete='CASCADE'),
    )
    
    # Indexes
    op.create_index('idx_gen_run_agent', 'scenario_generation_runs', ['agent_id'])
    op.create_index('idx_gen_run_suite', 'scenario_generation_runs', ['scenario_suite_id'])
    op.create_index('idx_gen_run_status', 'scenario_generation_runs', ['status'])


def downgrade() -> None:
    """Drop Part 2 tables."""
    op.drop_table('scenario_generation_runs')
    op.drop_table('scenarios')
    op.drop_table('scenario_suites')
    op.drop_table('test_strategies')
    op.drop_table('risk_profiles')
    op.drop_table('agent_capability_profiles')
