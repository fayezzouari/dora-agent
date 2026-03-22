import os

try:
    from .tools import RobotTools
except ImportError:
    from tools import RobotTools  # type: ignore[no-redef]


def _make_smolagents_tools(robot_tools: RobotTools) -> list:
    """Create smolagents Tool instances wrapping RobotTools methods."""
    from smolagents import Tool

    class MoveRobotTool(Tool):
        name = "move_robot"
        description = (
            "Move the robot at the specified velocity. "
            "vx is forward/backward speed in m/s (negative = backward). "
            "wz is turning speed in rad/s (positive = left, negative = right). "
            "Returns a confirmation string."
        )
        inputs = {
            "vx": {"type": "number", "description": "Forward velocity in m/s (-2.0 to 2.0)"},
            "wz": {"type": "number", "description": "Angular velocity in rad/s (-3.14 to 3.14)", "nullable": True},
            "duration": {"type": "number", "description": "Seconds to move before stopping automatically. Use 0 to keep moving.", "nullable": True},
        }
        output_type = "string"

        def __init__(self, rt: RobotTools) -> None:
            self._rt = rt
            super().__init__()

        def forward(self, vx: float, wz: float = 0.0, duration: float = 2.0) -> str:
            return self._rt.move(vx=vx, wz=wz, duration=duration)

    class StopRobotTool(Tool):
        name = "stop_robot"
        description = "Stop the robot immediately. Use this to halt all motion."
        inputs = {}
        output_type = "string"

        def __init__(self, rt: RobotTools) -> None:
            self._rt = rt
            super().__init__()

        def forward(self) -> str:
            return self._rt.stop()

    class GetRobotStateTool(Tool):
        name = "get_robot_state"
        description = (
            "Get the current position, heading, and velocity of the robot. "
            "Returns a human-readable status string."
        )
        inputs = {}
        output_type = "string"

        def __init__(self, rt: RobotTools) -> None:
            self._rt = rt
            super().__init__()

        def forward(self) -> str:
            return self._rt.get_state()

    return [
        MoveRobotTool(robot_tools),
        StopRobotTool(robot_tools),
        GetRobotStateTool(robot_tools),
    ]


class SmolagentsAgent:
    """
    LLM-powered agent using smolagents ToolCallingAgent.
    Requires HUGGINGFACE_API_TOKEN or ANTHROPIC_API_KEY environment variable.
    """

    def __init__(self, robot_tools: RobotTools) -> None:
        try:
            from smolagents import CodeAgent, InferenceClientModel, OpenAIServerModel
        except ImportError:
            raise ImportError(
                "smolagents is not installed. Run: pip install 'dora-agentic-control[smolagents]'"
            )

        tools = _make_smolagents_tools(robot_tools)

        groq_key = os.environ.get("GROQ_API_KEY")
        hf_token = os.environ.get("HUGGINGFACE_API_TOKEN")
        model_id = os.environ.get("SMOLAGENTS_MODEL", "Qwen/Qwen2.5-72B-Instruct")

        if groq_key:
            # Groq exposes an OpenAI-compatible API — no extra dependency needed.
            model = OpenAIServerModel(
                model_id=os.environ.get("SMOLAGENTS_MODEL", "llama-3.3-70b-versatile"),
                api_base="https://api.groq.com/openai/v1",
                api_key=groq_key,
            )
        elif hf_token:
            model = InferenceClientModel(model_id=model_id, token=hf_token)
        else:
            raise ValueError(
                "No API key found. Set GROQ_API_KEY or HUGGINGFACE_API_TOKEN, "
                "or use AGENT_TYPE=mock for offline operation."
            )

        self._agent = CodeAgent(tools=tools, model=model, max_steps=3)

    def run(self, user_input: str) -> str:
        system_prompt = (
            "You are controlling a simulated mobile robot. "
            "Use the available tools to respond to the user's command. "
            "Always call a tool to act on movement commands."
        )
        result = self._agent.run(f"{system_prompt}\n\nCommand: {user_input}")
        return str(result)
