"""
CLI interface node — reads user commands from a named pipe and prints agent responses.

Dora spawns nodes as child processes whose stdin is not connected to the terminal.
This node uses a FIFO (named pipe) so commands can be sent from any terminal:

    echo "move forward" > /tmp/dora-robot

Inputs:
  agent_response : string array — response text from the agent bridge

Outputs:
  user_command   : string array — command text entered by the user
"""

import os
import queue
import stat
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from settings import ROBOT_FIFO

import pyarrow as pa
from dora import Node

FIFO_PATH = ROBOT_FIFO

BANNER = (
    "Agentic Dora — Robot Control\n"
    f"Send commands via:  echo 'move forward' > {FIFO_PATH}\n"
    "Commands: move forward, move backward, turn left, turn right, stop, status\n"
)


def _ensure_fifo() -> None:
    if os.path.exists(FIFO_PATH):
        if not stat.S_ISFIFO(os.stat(FIFO_PATH).st_mode):
            os.remove(FIFO_PATH)
            os.mkfifo(FIFO_PATH)
    else:
        os.mkfifo(FIFO_PATH)


def _fifo_reader(q: queue.Queue) -> None:
    """Continuously reopen the FIFO so it survives multiple writers."""
    while True:
        try:
            with open(FIFO_PATH, "r") as fifo:
                for line in fifo:
                    line = line.strip()
                    if line:
                        q.put(line)
        except (OSError, KeyboardInterrupt):
            break


def main() -> None:
    _ensure_fifo()

    node = Node()
    cmd_queue: queue.Queue = queue.Queue()

    reader_thread = threading.Thread(target=_fifo_reader, args=(cmd_queue,), daemon=True)
    reader_thread.start()

    print(BANNER, flush=True)

    while True:
        while True:
            try:
                line = cmd_queue.get_nowait()
            except queue.Empty:
                break
            if line.lower() in ("quit", "exit"):
                return
            print(f"Sending: {line}", flush=True)
            node.send_output("user_command", pa.array([line], type=pa.string()))

        event = node.next(timeout=0.05)

        if event is None:
            continue

        if event["type"] == "STOP":
            break

        if event["type"] == "INPUT" and event["id"] == "agent_response":
            response = event["value"][0].as_py()
            print(f"Agent: {response}", flush=True)

    try:
        os.remove(FIFO_PATH)
    except OSError:
        pass


if __name__ == "__main__":
    main()
