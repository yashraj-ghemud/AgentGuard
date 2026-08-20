"""Initial schema with agents, agent_versions, and tools tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-08-18 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create initial database schema.
    
    Module Ownership:
    - agents table: Agent Registry module
    - agent_versions table: Agent Versioning module
    - tools table: Tool Registry module
    """
    
    # Create entity_status enum type
    op.execute("""
        CREATE TYPE entity_status AS ENUM ('active', 'inactive', 'archived', 'deleted')
    """)
    
    # ========================================================================
    # Agent Registry Module - agents table
    # ========================================================================
    op.create_table(
        'agents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('endpoint_url', sa.Text, nullable=False),
        sa.Column('execution_mode', sa.String(50), nullable=False),
        sa.Column('purpose', sa.Text),
        sa.Column('status', sa.Enum('active', 'inactive', 'archived', 'deleted', name='entity_status'), 
                  nullable=False, server_default='active'),
        sa.Column('risk_profile', JSONB, default={}),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('workspace_id', UUID(as_uuid=True)),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    
    # Indexes for agents table
    op.create_index('idx_agents_name', 'agents', ['name'])
    op.create_index('idx_agents_status', 'agents', ['status'])
    op.create_index('idx_agents_workspace_id', 'agents', ['workspace_id'])
    op.create_index('idx_agents_execution_mode', 'agents', ['execution_mode'])
    
    # ========================================================================
    # Agent Versioning Module - agent_versions table
    # ========================================================================
    op.create_table(
        'agent_versions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', UUID(as_uuid=True), nullable=False),
        sa.Column('version_number', sa.String(100), nullable=False),
        sa.Column('snapshot', JSONB, nullable=False),
        sa.Column('notes', sa.Text),
        sa.Column('snapshot_metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
    )
    
    # Indexes for agent_versions table
    op.create_index('idx_agent_versions_agent_id', 'agent_versions', ['agent_id'])
    op.create_index('idx_agent_versions_created_at', 'agent_versions', ['created_at'])
    
    # Unique constraint on (agent_id, version_number)
    op.create_unique_constraint(
        'uk_agent_versions_agent_version',
        'agent_versions',
        ['agent_id', 'version_number']
    )
    
    # ========================================================================
    # Tool Registry Module - tools table
    # ========================================================================
    op.create_table(
        'tools',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('agent_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=False),
        sa.Column('input_schema', JSONB, nullable=False),
        sa.Column('output_schema', JSONB),
        sa.Column('risk_level', sa.String(50), nullable=False),
        sa.Column('is_destructive', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_reversible', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('requires_confirmation', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('timeout_seconds', sa.Integer),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('metadata', JSONB, default={}),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
    )
    
    # Indexes for tools table
    op.create_index('idx_tools_agent_id', 'tools', ['agent_id'])
    op.create_index('idx_tools_risk_level', 'tools', ['risk_level'])
    op.create_index('idx_tools_status', 'tools', ['status'])
    
    # Unique constraint on (agent_id, name)
    op.create_unique_constraint(
        'uk_tools_agent_name',
        'tools',
        ['agent_id', 'name']
    )


def downgrade() -> None:
    """Drop all tables and types."""
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('tools')
    op.drop_table('agent_versions')
    op.drop_table('agents')
    
    # Drop enum type
    op.execute('DROP TYPE entity_status')
