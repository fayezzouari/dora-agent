# Agentic Dora — Agent-Driven Robot Control

A bridge between an AI agent framework and the [Dora](https://dora-rs.ai) robotics dataflow system.
Send natural language commands from a CLI and watch a simulated robot execute them.

## Architecture

```
./robot (CLI)
  |
  v
/tmp/dora-robot (FIFO)
  |
  v
[cli_interface] --user_command--> [agent_bridge] --velocity_cmd/stop_cmd--> [simulation]
      ^                                  |                                        |
      |                                  |                                        |
[agent_response] <--------------------[agent]                             [robot_state]
                                   (mock or Groq)
```

**Nodes:**
- `cli_interface` — reads commands from a named pipe (`/tmp/dora-robot`), prints agent responses
- `agent_bridge` — runs the agent in a background thread, dispatches motor commands in real-time
- `simulation` — headless kinematic robot model; loads PyBullet GUI when `PYBULLET_GUI=1`

**Messages:**
| ID | Type | Format |
|---|---|---|
| `user_command` | string[1] | user text |
| `agent_response` | string[1] | agent reply |
| `velocity_cmd` | float32[3] | `[vx, vy, wz]` m/s, m/s, rad/s |
| `stop_cmd` | int8[1] | stop signal |
| `robot_state` | float32[10] | `[px,py,pz, ox,oy,oz,ow, vx,vy,vz]` |

## Prerequisites

- Python 3.10+
- Dora CLI: `pip install dora-rs-cli`

## Setup

```bash
pip install -e .

pip install -e ".[smolagents]"
```

## Running

### Default (mock agent, no API key needed)

```bash
dora run dataflow.yml
```

### With PyBullet GUI

```bash
PYBULLET_GUI=1 dora run dataflow.yml
```

The camera starts top-down. Use mouse to rotate/zoom freely — the camera follows the robot position automatically.

### With local Ollama (default LLM backend)

```bash
AGENT_TYPE=smolagents dora run dataflow.yml
```

Requires [Ollama](https://ollama.com) running locally with `qwen3:1.7b` pulled:

```bash
ollama pull qwen3:1.7b
```

Override the model with:

```bash
SMOLAGENTS_MODEL=qwen3:4b AGENT_TYPE=smolagents dora run dataflow.yml
```

### With Groq LLM agent

```bash
export GROQ_API_KEY=gsk_...
AGENT_TYPE=smolagents dora run dataflow.yml
```

Default model is `llama-3.3-70b-versatile`. Override with:

```bash
SMOLAGENTS_MODEL=mixtral-8x7b-32768 AGENT_TYPE=smolagents dora run dataflow.yml
```

## Sending Commands

Use the included `robot` CLI to send commands to the running pipeline.

### Single command

```bash
./robot stop
./robot move forward
./robot "move in the shape of a square"
./robot "move forward for 5 seconds"
```

### Interactive session

```bash
./robot
> move forward
> turn left
> move in the shape of a square
> status
> quit
```

To use `robot` from anywhere:

```bash
export PATH="$PATH:/home/fayez/projects/dora-agentic-control"
```

### Custom pipe path

```bash
ROBOT_FIFO=/tmp/my-robot dora run dataflow.yml
ROBOT_FIFO=/tmp/my-robot ./robot "move forward"
```

## Example Commands

| Command | Effect |
|---|---|
| `move forward` | Move forward at 0.5 m/s for 2 s |
| `move forward at 1.5` | Move forward at 1.5 m/s for 2 s |
| `move forward for 5 seconds` | Move forward for 5 s |
| `turn left` | Rotate exactly 90° counterclockwise (closed-loop) |
| `turn right` | Rotate exactly 90° clockwise (closed-loop) |
| `stop` | Halt immediately |
| `status` | Report current position and heading |
| `move in the shape of a square` | LLM plans and executes a square path |

## Running Tests

```bash
pip install pytest
pytest
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `AGENT_TYPE` | `mock` | Agent backend: `mock` or `smolagents` |
| `PYBULLET_GUI` | `0` | Set to `1` to open PyBullet GUI window |
| `GROQ_API_KEY` | — | Groq API key for LLM agent |
| `SMOLAGENTS_MODEL` | `qwen3:1.7b` (Ollama) / `llama-3.3-70b-versatile` (Groq) | Model ID for the active backend |
| `ROBOT_FIFO` | `/tmp/dora-robot` | Named pipe path for robot commands |

## Extending

**Adding a new robot tool:**

1. Add a method to `RobotTools` in `nodes/agent_bridge/tools.py`
2. Add a keyword pattern in `MockAgent._PATTERNS` in `nodes/agent_bridge/mock_agent.py`
3. Add a `Tool` subclass in `nodes/agent_bridge/smolagents_agent.py` and include it in `_make_smolagents_tools()`

**Swapping the simulation:**

Replace `nodes/simulation/node.py` with any node that:
- Accepts `velocity_cmd` (float32[3]) and `stop_cmd` (int8[1]) inputs
- Publishes `robot_state` (float32[10]) on the `tick` input

The rest of the pipeline is unchanged.
