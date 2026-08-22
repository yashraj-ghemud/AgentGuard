"""Create one explicitly local development agent from environment variables.

This script does not invent production agents, models, releases, or public URLs.
Use it only for local development when you want a database record to exercise
AgentGuard's registry and evaluation UI.

Required environment variables:
    SEED_AGENT_ENDPOINT: reachable HTTP endpoint for your own test agent.

Optional:
    SEED_AGENT_NAME: display name for the local agent.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from sqlalchemy.orm import Session

# Allow running as `python scripts/seed_data.py` from Backend/.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config.settings import get_settings  # noqa: E402
from core.database.base import Base, get_engine  # noqa: E402
from modules.agent_registry.domain.models import Agent  # noqa: E402
from shared.types import EntityStatus  # noqa: E402
from shared.utils import generate_id, utc_now  # noqa: E402


def seed_database() -> None:
    """Seed one local development agent without fabricated production data."""
    endpoint = os.getenv("SEED_AGENT_ENDPOINT", "").strip()
    if not endpoint:
        raise SystemExit(
            "SEED_AGENT_ENDPOINT is required. Point it at an HTTP test agent you control; "
            "no public/example endpoint is hardcoded."
        )

    settings = get_settings()
    engine = get_engine()
    Base.metadata.create_all(engine)

    agent_id = generate_id()
    workspace_id = generate_id()
    name = os.getenv("SEED_AGENT_NAME", "Local Test Agent").strip() or "Local Test Agent"
    now = utc_now()

    agent = Agent(
        id=agent_id,
        name=name,
        description="Development-only agent record created from explicit local configuration.",
        endpoint_url=endpoint,
        execution_mode="http",
        purpose="Exercise AgentGuard locally with an agent endpoint owned by the developer.",
        status=EntityStatus.ACTIVE,
        risk_profile={
            "risk_level": "medium",
            "requires_human_approval": True,
            "max_execution_time_seconds": 60,
        },
        agent_metadata={"environment": "development"},
        workspace_id=workspace_id,
        created_at=now,
        updated_at=now,
    )

    with Session(engine) as session:
        session.add(agent)
        session.commit()

    print("Local development agent created.")
    print(f"Agent ID: {agent_id}")
    print(f"Endpoint: {endpoint}")
    print("Open /docs or the frontend evaluation console to use it.")
    print(f"Database settings loaded for environment: {settings.ENVIRONMENT}")


if __name__ == "__main__":
    seed_database()
