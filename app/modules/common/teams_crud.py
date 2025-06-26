"""
CRUD básico para Team
Sin validaciones, operaciones directas con DB
"""

import sqlalchemy as sa
from typing import Dict, Optional
from .db import engine, teams_table, tier_capacity_table
from .models import Team


def create_team(team: Team) -> int:
    """Crear team en DB"""
    with engine.begin() as conn:
        # Insert team
        result = conn.execute(
            teams_table.insert().values(
                name=team.name,
                total_devs=team.total_devs,
                busy_devs=team.busy_devs
            ).returning(teams_table.c.id)
        )
        team_id = result.scalar()
        
        # Insert tier capacities
        for tier, hours in team.tier_capacities.items():
            conn.execute(
                tier_capacity_table.insert().values(
                    team_id=team_id,
                    tier=tier,
                    hours_per_person=hours
                )
            )
        
        return team_id


def read_team(team_id: int) -> Optional[Team]:
    """Leer team desde DB"""
    with engine.begin() as conn:
        # Get team data
        team_result = conn.execute(
            sa.select(
                teams_table.c.id,
                teams_table.c.name,
                teams_table.c.total_devs,
                teams_table.c.busy_devs
            ).where(teams_table.c.id == team_id)
        ).first()
        
        if not team_result:
            return None
        
        # Get tier capacities
        tier_results = conn.execute(
            sa.select(
                tier_capacity_table.c.tier,
                tier_capacity_table.c.hours_per_person
            ).where(tier_capacity_table.c.team_id == team_id)
        ).fetchall()
        
        tier_capacities = {
            row.tier: row.hours_per_person 
            for row in tier_results
        }
        
        return Team(
            id=team_result.id,
            name=team_result.name,
            total_devs=team_result.total_devs,
            busy_devs=team_result.busy_devs,
            tier_capacities=tier_capacities
        )


def read_all_teams() -> Dict[int, Team]:
    """Leer todos los teams desde DB"""
    with engine.begin() as conn:
        # Get all teams
        teams_results = conn.execute(
            sa.select(
                teams_table.c.id,
                teams_table.c.name,
                teams_table.c.total_devs,
                teams_table.c.busy_devs
            ).order_by(teams_table.c.name)
        ).fetchall()
        
        # Get all tier capacities
        tier_results = conn.execute(
            sa.select(
                tier_capacity_table.c.team_id,
                tier_capacity_table.c.tier,
                tier_capacity_table.c.hours_per_person
            )
        ).fetchall()
        
        # Group tier capacities by team_id
        tier_by_team = {}
        for row in tier_results:
            if row.team_id not in tier_by_team:
                tier_by_team[row.team_id] = {}
            tier_by_team[row.team_id][row.tier] = row.hours_per_person
        
        # Build teams dict
        teams = {}
        for row in teams_results:
            teams[row.id] = Team(
                id=row.id,
                name=row.name,
                total_devs=row.total_devs,
                busy_devs=row.busy_devs,
                tier_capacities=tier_by_team.get(row.id, {})
            )
        
        return teams


def update_team(team: Team):
    """Actualizar team en DB"""
    with engine.begin() as conn:
        # Update team
        conn.execute(
            teams_table.update()
            .where(teams_table.c.id == team.id)
            .values(
                name=team.name,
                total_devs=team.total_devs,
                busy_devs=team.busy_devs
            )
        )
        
        # Delete existing tier capacities
        conn.execute(
            tier_capacity_table.delete()
            .where(tier_capacity_table.c.team_id == team.id)
        )
        
        # Insert new tier capacities
        for tier, hours in team.tier_capacities.items():
            conn.execute(
                tier_capacity_table.insert().values(
                    team_id=team.id,
                    tier=tier,
                    hours_per_person=hours
                )
            )


def delete_team(team_id: int):
    """Borrar team de DB"""
    with engine.begin() as conn:
        # Delete tier capacities first (FK constraint)
        conn.execute(
            tier_capacity_table.delete()
            .where(tier_capacity_table.c.team_id == team_id)
        )
        
        # Delete team
        conn.execute(
            teams_table.delete()
            .where(teams_table.c.id == team_id)
        )