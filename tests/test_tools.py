import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "nodes", "agent_bridge"))

from tools import RobotState, RobotCommand, RobotTools
import math


def make_tools():
    state = RobotState()
    command = RobotCommand()
    tools = RobotTools(state, command)
    return state, command, tools


def test_robot_state_update_from_flat():
    state = RobotState()
    state.update_from_flat([1.0, 2.0, 3.0, 0.0, 0.0, 0.0, 1.0, 0.1, 0.2, 0.3])
    assert state.position == (1.0, 2.0, 3.0)
    assert state.orientation == (0.0, 0.0, 0.0, 1.0)
    assert state.velocity == (0.1, 0.2, 0.3)


def test_robot_state_to_description():
    state = RobotState()
    state.update_from_flat([1.5, 2.5, 0.25, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
    desc = state.to_description()
    assert "1.50" in desc
    assert "2.50" in desc


def test_robot_state_heading():
    state = RobotState()
    # No rotation: heading should be 0 degrees
    state.update_from_flat([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
    assert abs(state.heading_degrees()) < 0.1


def test_move_tool_forward():
    state, command, tools = make_tools()
    result = tools.move(vx=0.5)
    assert command.command_type == "move"
    assert command.velocity[0] == pytest_approx(0.5)
    assert "0.50" in result


def test_move_tool_clamps_speed():
    state, command, tools = make_tools()
    tools.move(vx=99.0)
    assert command.velocity[0] <= 2.0


def test_stop_tool():
    state, command, tools = make_tools()
    tools.move(vx=1.0)
    result = tools.stop()
    assert command.command_type == "stop"
    assert command.velocity == (0.0, 0.0, 0.0)
    assert "stopped" in result.lower()


def test_get_state_tool_returns_string():
    state, command, tools = make_tools()
    result = tools.get_state()
    assert isinstance(result, str)
    assert len(result) > 0


def test_robot_command_reset():
    command = RobotCommand(command_type="move", velocity=(1.0, 0.0, 0.0))
    command.reset()
    assert command.command_type == "none"
    assert command.velocity == (0.0, 0.0, 0.0)


def pytest_approx(value, rel=1e-3):
    import math
    class Approx:
        def __eq__(self, other):
            return abs(other - value) <= rel * max(abs(value), abs(other), 1e-10)
        def __repr__(self):
            return f"~{value}"
    return Approx()
