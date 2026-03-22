"""
Agent bridge node — connects the AI agent to the Dora dataflow.

Inputs:
  user_command  : string array  — command from the CLI interface
  robot_state   : float32[10]   — [px,py,pz, ox,oy,oz,ow, vx,vy,vz] from simulation
  tick          : timer         — periodic heartbeat for polling the agent future

Outputs:
  velocity_cmd  : float32[3]    — [vx, vy, wz] sent to simulation
  stop_cmd      : int8[1]       — stop signal sent to simulation
  agent_response: string array  — response text sent back to CLI
"""

import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

import pyarrow as pa
from dora import Node

from tools import RobotState, RobotCommand, RobotTools
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
    command = RobotCommand()
    robot_tools = RobotTools(state, command)
    agent = _create_agent(robot_tools)

    executor = ThreadPoolExecutor(max_workers=1)
    pending_future: Optional[Future] = None
    state_lock = threading.Lock()

    def run_agent(text: str) -> str:
        return agent.run(text)

    def dispatch_command() -> None:
        vx, vy, wz = command.velocity
        if command.command_type == "move":
            node.send_output(
                "velocity_cmd",
                pa.array([vx, vy, wz], type=pa.float32()),
            )
        elif command.command_type == "stop":
            node.send_output("stop_cmd", pa.array([1], type=pa.int8()))

    while True:
        event = node.next(timeout=0.01)

        if event is None:
            if pending_future is not None and pending_future.done():
                try:
                    response = pending_future.result()
                    dispatch_command()
                    node.send_output(
                        "agent_response",
                        pa.array([response], type=pa.string()),
                    )
                except Exception as exc:
                    node.send_output(
                        "agent_response",
                        pa.array([f"Error: {exc}"], type=pa.string()),
                    )
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
                pending_future = executor.submit(run_agent, text)

        elif input_id == "tick":
            if pending_future is not None and pending_future.done():
                try:
                    response = pending_future.result()
                    dispatch_command()
                    node.send_output(
                        "agent_response",
                        pa.array([response], type=pa.string()),
                    )
                except Exception as exc:
                    node.send_output(
                        "agent_response",
                        pa.array([f"Error: {exc}"], type=pa.string()),
                    )
                pending_future = None

    executor.shutdown(wait=False)


if __name__ == "__main__":
    main()
