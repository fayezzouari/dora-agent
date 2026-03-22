import queue
import sys
import os
import unittest.mock as mock
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "nodes", "agent_bridge"))

from tools import RobotState, RobotTools
from mock_agent import MockAgent


def make_agent():
    state = RobotState()
    cmd_queue = queue.Queue()
    tools = RobotTools(state, cmd_queue)
    agent = MockAgent(tools)
    return state, cmd_queue, tools, agent


def _run(agent, text):
    """Run agent with time.sleep patched out."""
    with mock.patch("time.sleep"):
        return agent.run(text)


def _first_cmd(cmd_queue):
    return cmd_queue.get_nowait()


def test_forward_command():
    _, cmd_queue, _, agent = make_agent()
    _run(agent, "move forward")
    cmd = _first_cmd(cmd_queue)
    assert cmd.type == "move"
    assert cmd.velocity[0] > 0


def test_backward_command():
    _, cmd_queue, _, agent = make_agent()
    _run(agent, "move backward")
    cmd = _first_cmd(cmd_queue)
    assert cmd.type == "move"
    assert cmd.velocity[0] < 0


def test_stop_command():
    _, cmd_queue, _, agent = make_agent()
    _run(agent, "stop")
    cmd = _first_cmd(cmd_queue)
    assert cmd.type == "stop"


def test_turn_left():
    _, cmd_queue, _, agent = make_agent()
    _run(agent, "turn left")
    cmd = _first_cmd(cmd_queue)
    assert cmd.type == "move"
    assert cmd.velocity[2] > 0


def test_turn_right():
    _, cmd_queue, _, agent = make_agent()
    _run(agent, "turn right")
    cmd = _first_cmd(cmd_queue)
    assert cmd.type == "move"
    assert cmd.velocity[2] < 0


def test_state_query():
    state, cmd_queue, _, agent = make_agent()
    state.update_from_flat([3.0, 4.0, 0.25, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0])
    result = _run(agent, "what is your status")
    assert cmd_queue.empty()
    assert "3.00" in result or "Position" in result


def test_speed_modifier():
    _, cmd_queue, _, agent = make_agent()
    _run(agent, "move forward at 1.5")
    cmd = _first_cmd(cmd_queue)
    assert abs(cmd.velocity[0] - 1.5) < 0.01


def test_unknown_command():
    _, cmd_queue, _, agent = make_agent()
    result = _run(agent, "do a backflip")
    assert cmd_queue.empty()
    assert "unknown" in result.lower() or "command" in result.lower()


def test_halt_alias():
    _, cmd_queue, _, agent = make_agent()
    _run(agent, "halt")
    cmd = _first_cmd(cmd_queue)
    assert cmd.type == "stop"


def test_reverse_alias():
    _, cmd_queue, _, agent = make_agent()
    _run(agent, "reverse")
    cmd = _first_cmd(cmd_queue)
    assert cmd.type == "move"
    assert cmd.velocity[0] < 0


def test_movement_produces_stop_after_duration():
    _, cmd_queue, _, agent = make_agent()
    with mock.patch("time.sleep"):
        agent.run("move forward")
    assert cmd_queue.qsize() == 2
    assert cmd_queue.get_nowait().type == "move"
    assert cmd_queue.get_nowait().type == "stop"


def test_custom_duration():
    _, cmd_queue, _, agent = make_agent()
    with mock.patch("time.sleep") as sleep_mock:
        agent.run("move forward for 5 seconds")
    sleep_mock.assert_called_once_with(5.0)
