import queue
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "nodes", "agent_bridge"))

from tools import RobotState, RobotTools, Command


def make_tools():
    state = RobotState()
    cmd_queue = queue.Queue()
    tools = RobotTools(state, cmd_queue)
    return state, cmd_queue, tools


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
    state.update_from_flat([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
    assert abs(state.heading_degrees()) < 0.1


def test_move_tool_puts_command():
    _, cmd_queue, tools = make_tools()
    tools.move(vx=0.5)
    assert not cmd_queue.empty()
    cmd = cmd_queue.get_nowait()
    assert cmd.type == "move"
    assert abs(cmd.velocity[0] - 0.5) < 0.01


def test_move_tool_clamps_speed():
    _, cmd_queue, tools = make_tools()
    tools.move(vx=99.0)
    cmd = cmd_queue.get_nowait()
    assert cmd.velocity[0] <= 2.0


def test_stop_tool_puts_command():
    _, cmd_queue, tools = make_tools()
    tools.stop()
    cmd = cmd_queue.get_nowait()
    assert cmd.type == "stop"


def test_get_state_tool_returns_string():
    _, _, tools = make_tools()
    result = tools.get_state()
    assert isinstance(result, str)
    assert len(result) > 0


def test_move_with_duration_puts_two_commands():
    _, cmd_queue, tools = make_tools()
    # Use a tiny duration so the test doesn't actually sleep long
    # We monkeypatch time.sleep to avoid waiting
    import unittest.mock as mock
    with mock.patch("time.sleep"):
        tools.move(vx=0.5, duration=2.0)
    assert cmd_queue.qsize() == 2
    first = cmd_queue.get_nowait()
    second = cmd_queue.get_nowait()
    assert first.type == "move"
    assert second.type == "stop"
