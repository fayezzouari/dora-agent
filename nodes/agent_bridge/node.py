"""
Agent bridge node — connects the AI agent to the Dora dataflow.

Inputs:
  user_command  : string array  — command from the CLI interface
  robot_state   : float32[10]   — [px,py,pz, ox,oy,oz,ow, vx,vy,vz] from simulation
  tick          : timer         — periodic heartbeat

Outputs:
  velocity_cmd  : float32[3]    — [vx, vy, wz] sent to simulation
  stop_cmd      : int8[1]       — stop signal sent to simulation
  agent_response: string array  — response text sent back to CLI
"""

import os
import queue as std_queue
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

import pyarrow as pa
from dora import Node

from tools import RobotState, RobotTools
from mock_agent import MockAgent


def _create_agent(robot_tools: RobotTools):
    agent_type = os.environ.get("AGENT_TYPE", "mock").lower()
    if agent_type == "mock":
        return MockAgent(robot_tools)
    if agent_type == "smolagents":
        from smolagents_agent import SmolagentsAgent
        return SmolagentsAgent(robot_tools)
    raise ValueError(f"Unknown AGENT_TYPE={agent_type!r}. Use 'mock' or 'smolagents'.")


def main() -> None:
    node = Node()

    state = RobotState()
    cmd_queue: std_queue.Queue = std_queue.Queue()
    robot_tools = RobotTools(state, cmd_queue)
    agent = _create_agent(robot_tools)

    executor = ThreadPoolExecutor(max_workers=1)
    pending_future: Optional[Future] = None
    state_lock = threading.Lock()

    def drain_commands() -> None:
        """Flush all pending robot commands from the queue to the Dora outputs."""
        while True:
            try:
                cmd = cmd_queue.get_nowait()
            except std_queue.Empty:
                break
            if cmd.type == "move":
                node.send_output(
                    "velocity_cmd",
                    pa.array(list(cmd.velocity), type=pa.float32()),
                )
            elif cmd.type == "stop":
                node.send_output("stop_cmd", pa.array([1], type=pa.int8()))

    def finish_future(future: Future) -> None:
        try:
            response = future.result()
        except Exception as exc:
            response = f"Error: {exc}"
        drain_commands()
        node.send_output("agent_response", pa.array([response], type=pa.string()))

    while True:
        # Always drain any commands the agent thread produced before waiting.
        drain_commands()

        event = node.next(timeout=0.01)

        if event is None:
            if pending_future is not None and pending_future.done():
                finish_future(pending_future)
                pending_future = None
            continue

        if event["type"] == "STOP":
            break

        if event["type"] != "INPUT":
            continue

        input_id = event["id"]

        if input_id == "robot_state":
            with state_lock:
                state.update_from_flat(event["value"].to_pylist())

        elif input_id == "user_command":
            text = event["value"][0].as_py()
            if not text:
                continue
            if pending_future is not None and not pending_future.done():
                node.send_output(
                    "agent_response",
                    pa.array(
                        ["Still processing previous command, please wait."],
                        type=pa.string(),
                    ),
                )
            else:
                pending_future = executor.submit(agent.run, text)

        elif input_id == "tick":
            if pending_future is not None and pending_future.done():
                finish_future(pending_future)
                pending_future = None

    executor.shutdown(wait=False)


if __name__ == "__main__":
    main()
