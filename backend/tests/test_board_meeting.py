import pytest
from app.application.orchestrator import check_board_iteration, get_next_board_agent, route_board_meeting

def test_check_board_iteration_first_round():
    # En la primera iteración, si faltan agentes, debe continuar
    state = {
        "board_iteration": 0,
        "board_max_iterations": 2,
        "board_agents_done": ["CEO", "CTO"]
    }
    assert check_board_iteration(state) == "continue_iteration"

def test_check_board_iteration_end_of_round_next_iteration():
    # Si todos respondieron y hay más iteraciones, debe avanzar iteración
    state = {
        "board_iteration": 0,
        "board_max_iterations": 2,
        "board_agents_done": ["CEO", "CTO", "CFO", "CMO"]
    }
    assert check_board_iteration(state) == "next_iteration"

def test_check_board_iteration_end_of_all_rounds_conclusion():
    # Si todos respondieron en la última iteración, debe ir a conclusión
    state = {
        "board_iteration": 1,
        "board_max_iterations": 2,
        "board_agents_done": ["CEO", "CTO", "CFO", "CMO"]
    }
    assert check_board_iteration(state) == "conclusion"

def test_get_next_board_agent():
    state = {
        "board_agents_done": ["CEO", "CTO"]
    }
    assert get_next_board_agent(state) == "CFO"
    
    state_2 = {
        "board_agents_done": ["CEO", "CTO", "CFO"]
    }
    assert get_next_board_agent(state_2) == "CMO"

def test_route_board_meeting():
    state = {
        "board_iteration": 0,
        "board_max_iterations": 1,
        "board_agents_done": ["CEO"]
    }
    assert route_board_meeting(state) == "cto_board"

    state_done = {
        "board_iteration": 0,
        "board_max_iterations": 1,
        "board_agents_done": ["CEO", "CTO", "CFO", "CMO"]
    }
    assert route_board_meeting(state_done) == "conclusion"
