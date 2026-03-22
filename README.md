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
                                   (mock or LLM)
```

**Nodes:**
- `cli_interface` — reads commands from a named pipe (`/tmp/dora-robot`), prints agent responses
- `agent_bridge` — dispatches commands to the agent, translates results to motor commands
- `simulation` — kinematic robot model in PyBullet, publishes pose/velocity state

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
- `dora-rs` CLI: `pip install dora-rs-cli` (provides the `dora` command)

## Setup

```bash
# Install Python dependencies
pip install -e .

# For LLM-powered agent (optional)
pip install -e ".[smolagents]"
```

## Running

### Default (mock agent, no API key needed)

```bash
dora run dataflow.yml
```

### With PyBullet GUI (visual simulation)

```bash
PYBULLET_GUI=1 dora run dataflow.yml
```

### With LLM-powered agent (Hugging Face)

```bash
export HUGGINGFACE_API_TOKEN=hf_...
AGENT_TYPE=smolagents dora run dataflow.yml
```

### With LLM-powered agent (Anthropic)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
AGENT_TYPE=smolagents dora run dataflow.yml
```

## Sending Commands

The pipeline reads commands from a named pipe at `/tmp/dora-robot`.
Use the included `robot` CLI to send them — no need to type `echo ... > /tmp/dora-robot` manually.

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

To use `robot` from anywhere, add the project directory to your PATH:

```bash
export PATH="$PATH:/home/fayez/projects/dora-agentic-control"
```

### Direct pipe (alternative)

```bash
echo "move forward" > /tmp/dora-robot
```

Use a custom pipe path with:

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
| `turn left` | Rotate 90° counterclockwise |
| `turn right` | Rotate 90° clockwise |
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
| `HUGGINGFACE_API_TOKEN` | — | HF token for smolagents + HF Inference API |
| `ANTHROPIC_API_KEY` | — | Anthropic API key for Claude backend |
| `SMOLAGENTS_MODEL` | `Qwen/Qwen2.5-72B-Instruct` | HF model ID for smolagents |

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
