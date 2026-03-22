#!/usr/bin/env python3
"""
robot — send commands to the running Dora robot pipeline.

Usage:
  robot                          # interactive prompt
  robot move forward             # single command from arguments
  robot "move in the shape of a square"
"""

import os
import sys

FIFO_PATH = os.environ.get("ROBOT_FIFO", "/tmp/dora-robot")


def send(command: str) -> None:
    if not command.strip():
        return
    if not os.path.exists(FIFO_PATH):
        print(f"Error: pipeline not running (no FIFO at {FIFO_PATH})", file=sys.stderr)
        print("Start the pipeline first:  dora run dataflow.yml", file=sys.stderr)
        sys.exit(1)
    with open(FIFO_PATH, "w") as f:
        f.write(command.strip() + "\n")


def interactive() -> None:
    print(f"Robot CLI  (pipeline: {FIFO_PATH})")
    print("Commands: move forward, move backward, turn left, turn right, stop, status")
    print("Type 'quit' to exit.\n")
    while True:
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if cmd.lower() in ("quit", "exit"):
            break
        if cmd:
            send(cmd)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        send(" ".join(sys.argv[1:]))
    else:
        interactive()
