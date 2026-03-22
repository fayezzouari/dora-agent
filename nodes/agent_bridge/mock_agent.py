import re

try:
    from .tools import RobotTools
except ImportError:
    from tools import RobotTools  # type: ignore[no-redef]


class MockAgent:
    """
    Keyword-based agent that requires no external API.
    Parses user commands and calls RobotTools methods directly.
    """

    _PATTERNS = [
        (r"\bstop\b|\bhalt\b|\bfreeze\b", "stop"),
        (r"\bforward\b|\bahead\b|\bgo\s+straight\b", "forward"),
        (r"\bback(?:ward)?\b|\breverse\b|\bretreat\b", "backward"),
        (r"\bturn\s+left\b|\bgo\s+left\b|\bleft\b", "left"),
        (r"\bturn\s+right\b|\bgo\s+right\b|\bright\b", "right"),
        (r"\bstate\b|\bstatus\b|\bwhere\b|\bposition\b|\blocation\b", "state"),
    ]

    def __init__(self, robot_tools: RobotTools) -> None:
        self.tools = robot_tools

    def run(self, user_input: str) -> str:
        self.tools.command.reset()
        text = user_input.lower().strip()
        speed = self._extract_speed(text)

        for pattern, action in self._PATTERNS:
            if re.search(pattern, text):
                return self._dispatch(action, speed)

        return (
            "Unknown command. Try: move forward, move backward, turn left, "
            "turn right, stop, or ask for status."
        )

    def _extract_speed(self, text: str) -> float:
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m(?:/s)?)?", text)
        if match:
            speed = float(match.group(1))
            return max(0.1, min(2.0, speed))
        return 0.5

    def _dispatch(self, action: str, speed: float) -> str:
        if action == "stop":
            return self.tools.stop()
        if action == "forward":
            return self.tools.move(vx=speed)
        if action == "backward":
            return self.tools.move(vx=-speed)
        if action == "left":
            return self.tools.move(vx=0.0, wz=speed)
        if action == "right":
            return self.tools.move(vx=0.0, wz=-speed)
        if action == "state":
            return self.tools.get_state()
        return "No action taken."
