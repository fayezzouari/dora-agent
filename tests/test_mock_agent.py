import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "nodes", "agent_bridge"))

from tools import RobotState, RobotCommand, RobotTools
from mock_agent import MockAgent


def make_agent():
    state = RobotState()
    command = RobotCommand()
    tools = RobotTools(state, command)
    agent = MockAgent(tools)
    return state, command, tools, agent


def test_forward_command():
    _, command, _, agent = make_agent()
    agent.run("move forward")
    assert command.command_type == "move"
    assert command.velocity[0] > 0


def test_backward_command():
    _, command, _, agent = make_agent()
    agent.run("move backward")
    assert command.command_type == "move"
    assert command.velocity[0] < 0


def test_stop_command():
    _, command, _, agent = make_agent()
    agent.run("stop")
    assert command.command_type == "stop"


def test_turn_left():
    _, command, _, agent = make_agent()
    agent.run("turn left")
    assert command.command_type == "move"
    assert command.velocity[2] > 0  # wz positive = left


def test_turn_right():
    _, command, _, agent = make_agent()
    agent.run("turn right")
    assert command.command_type == "move"
    assert command.velocity[2] < 0  # wz negative = right


def test_state_query():
    state, command, _, agent = make_agent()
    state.update_from_flat([3.0, 4.0, 0.25, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
    result = agent.run("what is your status")
    assert command.command_type == "none"
    assert "3.00" in result or "Position" in result


def test_speed_modifier():
    _, command, _, agent = make_agent()
    agent.run("move forward at 1.5")
    assert command.command_type == "move"
    assert abs(command.velocity[0] - 1.5) < 0.01


def test_unknown_command():
    _, command, _, agent = make_agent()
    result = agent.run("do a backflip")
    assert command.command_type == "none"
    assert "unknown" in result.lower() or "command" in result.lower()


def test_halt_alias():
    _, command, _, agent = make_agent()
    agent.run("halt")
    assert command.command_type == "stop"


def test_reverse_alias():
    _, command, _, agent = make_agent()
    agent.run("reverse")
    assert command.command_type == "move"
    assert command.velocity[0] < 0


def test_command_resets_between_runs():
    _, command, _, agent = make_agent()
    agent.run("move forward")
    agent.run("where are you")
    assert command.command_type == "none"
