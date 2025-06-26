import streamlit as st
from datetime import date
from st_draggable_list import DraggableList
from modules.common.models import Project, Assignment
from modules.common.projects_crud import create_project, read_all_projects, update_project
from modules.common.assignments_crud import create_assignment, read_assignments_by_project, update_assignment
from modules.common.teams_crud import read_all_teams

def render_projects():
    st.header("Project Management")

    # ————————————————————————————————
    # 1) Create New Project (with default assignments)
    # ————————————————————————————————
    st.subheader("Create New Project")
    pname = st.text_input("Project Name", key="proj_name")
    start = st.date_input("Start Date", key="proj_start")

    if st.button("Create Project") and pname:
        # Get next priority
        projects = read_all_projects()
        next_priority = max([p.priority for p in projects.values()], default=0) + 1
        
        # Create project
        new_project = Project(
            id=0,  # Se asignará en DB
            name=pname,
            priority=next_priority,
            start_date=start,
            due_date_wo_qa=start,
            due_date_with_qa=start
        )
        proj_id = create_project(new_project)
        
        # Create default assignments for all teams
        teams = read_all_teams()
        for team_id, team in teams.items():
            # Get max tier for this team
            max_tier = max(team.tier_capacities.keys()) if team.tier_capacities else 1
            
            # Create assignment with defaults
            assignment = Assignment(
                id=0,  # Se asignará en DB
                project_id=proj_id,
                project_name=pname,
                project_priority=next_priority,
                team_id=team_id,
                team_name=team.name,
                tier=max_tier,
                devs_assigned=1.0,
                max_devs=1.0,
                estimated_hours=0,
                ready_to_start_date=start,
                assignment_start_date=start,
                status="Not Started",
                pending_hours=0,
                paused_on=None
            )
            create_assignment(assignment)
        
        st.success(f"Project '{pname}' created with ID {proj_id} and default assignments.")

    # --------------------------------------------
    # 2) Reorder Projects
    # --------------------------------------------
    st.subheader("Reorder Projects")
    projects = read_all_projects()
    if not projects:
        st.info("No projects to display.")
        return

    # Sort by priority for display
    sorted_projects = sorted(projects.values(), key=lambda p: p.priority)
    items = [{"id": p.id, "name": f"({p.priority}) {p.name}"} for p in sorted_projects]
    new_order = DraggableList(items, text_key="name", key="proj_sort")
    
    if st.button("Save Order"):
        for idx, itm in enumerate(new_order, start=1):
            project = projects[itm["id"]]
            project.priority = idx
            update_project(project)
        st.success("Project priorities updated.")

    # --------------------------------------------
    # 3) Edit Team Assignments
    # --------------------------------------------
    st.subheader("Edit Team Assignments")
    project_names = [p.name for p in sorted_projects]
    selected_name = st.selectbox(
        "Select Project to Edit",
        project_names,
        key="sel_proj_edit"
    )
    
    # Find selected project
    selected_project = None
    for project in projects.values():
        if project.name == selected_name:
            selected_project = project
            break
    
    if not selected_project:
        st.error("Project not found.")
        return

    # Get assignments for this project
    assignments = read_assignments_by_project(selected_project.id)
    if not assignments:
        st.info("No assignments for this project.")
        return

    # Get all teams for tier options
    teams = read_all_teams()

    # Para cada asignación, un expander con campos editables
    for assignment in assignments:
        with st.expander(assignment.team_name):
            # Get team for tier options
            team = teams.get(assignment.team_id)
            if not team:
                st.error(f"Team {assignment.team_id} not found.")
                continue
            
            # Tier: opciones filtradas por team_id
            tier_opts = list(team.tier_capacities.keys()) if team.tier_capacities else [1]
            tier_opts.sort()
            
            current_tier_index = tier_opts.index(assignment.tier) if assignment.tier in tier_opts else 0
            new_tier = st.selectbox(
                "Tier",
                tier_opts,
                index=current_tier_index,
                key=f"tier_{assignment.id}"
            )

            # Devs assigned / max devs
            new_assigned = st.number_input(
                "Devs Assigned",
                min_value=0.25,
                max_value=100.0,
                step=0.25,
                value=assignment.devs_assigned,
                key=f"assigned_{assignment.id}"
            )
            new_max = st.number_input(
                "Max Devs",
                min_value=0.25,
                max_value=100.0,
                step=0.25,
                value=assignment.max_devs,
                key=f"max_{assignment.id}"
            )

            # Estimated hours
            new_hours = st.number_input(
                "Estimated Hours",
                min_value=0,
                value=assignment.estimated_hours,
                key=f"hours_{assignment.id}"
            )

            # Ready to start date
            new_ready = st.date_input(
                "Ready to Start Date",
                value=assignment.ready_to_start_date or assignment.assignment_start_date,
                key=f"ready_{assignment.id}"
            )

            # Guardar cambios
            if st.button("Update Assignment", key=f"save_{assignment.id}"):
                updated_assignment = Assignment(
                    id=assignment.id,
                    project_id=assignment.project_id,
                    project_name=assignment.project_name,
                    project_priority=assignment.project_priority,
                    team_id=assignment.team_id,
                    team_name=assignment.team_name,
                    tier=int(new_tier),
                    devs_assigned=new_assigned,
                    max_devs=new_max,
                    estimated_hours=new_hours,
                    ready_to_start_date=new_ready,
                    assignment_start_date=assignment.assignment_start_date,
                    status=assignment.status,
                    pending_hours=assignment.pending_hours,
                    paused_on=assignment.paused_on
                )
                update_assignment(updated_assignment)
                st.success(f"Assignment for {assignment.team_name} updated.")
