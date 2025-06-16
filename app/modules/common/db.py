import os
import sqlalchemy as sa
from sqlalchemy import MetaData

db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("Environment variable DATABASE_URL not set")

engine = sa.create_engine(db_url, future=True)
metadata = MetaData()

projects_table = sa.Table(
    "projects", metadata, autoload_with=engine
)
teams_table = sa.Table(
    "teams", metadata, autoload_with=engine
)
project_team_assignments_table = sa.Table(
    "project_team_assignments", metadata, autoload_with=engine
)
tier_capacity_table = sa.Table(
    "tier_capacity", metadata, autoload_with=engine
)

def run(stmt):
    with engine.begin() as conn:
        conn.execute(stmt)