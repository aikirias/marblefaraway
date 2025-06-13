import os
import sqlalchemy as sa
from sqlalchemy import MetaData

# DB URL from env
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise RuntimeError("DATABASE_URL not set")

# Engine and metadata
engine = sa.create_engine(db_url, future=True)
metadata = MetaData()

# Table reflections
areas_table = sa.Table('areas', metadata, autoload_with=engine)
people_table = sa.Table('people', metadata, autoload_with=engine)
projects_table = sa.Table('projects', metadata, autoload_with=engine)

# Helper to run statements
def run(stmt):
    with engine.begin() as conn:
        conn.execute(stmt)