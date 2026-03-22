import math
import queue
import time

from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class RobotState:
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    orientation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    last_updated: float = field(default_factory=time.time)

    def update_from_flat(self, data: list) -> None:
        self.position = (float(data[0]), float(data[1]), float(data[2]))
        self.orientation = (float(data[3]), float(data[4]), float(data[5]), float(data[6]))
        self.velocity = (float(data[7]), float(data[8]), float(data[9]))
        self.last_updated = time.time()

    def heading_degrees(self) -> float:
        ox, oy, oz, ow = self.orientation
        siny_cosp = 2.0 * (ow * oz + ox * oy)
        cosy_cosp = 1.0 - 2.0 * (oy * oy + oz * oz)
        return math.degrees(math.atan2(siny_cosp, cosy_cosp))

    def to_description(self) -> str:
        px, py, pz = self.position
        vx, vy, _ = self.velocity
        heading = self.heading_degrees()
        return (
            f"Position: ({px:.2f}, {py:.2f}, {pz:.2f}) m, "
            f"Heading: {heading:.1f} deg, "
            f"Velocity: ({vx:.2f}, {vy:.2f}) m/s"
        )


@dataclass
class Command:
    type: str  # "move" | "stop"
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)


class RobotTools:
    """
    Robot tool implementations.
    Commands are pushed onto cmd_queue and dispatched by the Dora node's main loop
    so that each call takes effect immediately — even mid-agent-run.
    """

    def __init__(self, state: RobotState, cmd_queue: "queue.Queue[Command]") -> None:
        self.state = state
        self.cmd_queue = cmd_queue

    def move(
        self,
        vx: float,
        vy: float = 0.0,
        wz: float = 0.0,
        duration: float = 0.0,
    ) -> str:
        """
        Move the robot. vx=forward (m/s), wz=turn (rad/s).
        duration>0: move for that many seconds then stop automatically.
        duration=0: keep moving until the next command.
        """
        vx = float(max(-2.0, min(2.0, vx)))
        vy = float(max(-2.0, min(2.0, vy)))
        wz = float(max(-3.14, min(3.14, wz)))
        duration = float(max(0.0, min(30.0, duration)))

        self.cmd_queue.put(Command("move", (vx, vy, wz)))

        if duration > 0:
            time.sleep(duration)
            self.cmd_queue.put(Command("stop"))

        parts = []
        if abs(vx) > 0.01:
            parts.append(f"vx={vx:.2f} m/s")
        if abs(vy) > 0.01:
            parts.append(f"vy={vy:.2f} m/s")
        if abs(wz) > 0.01:
            parts.append(f"wz={wz:.2f} rad/s")
        desc = ", ".join(parts) if parts else "stationary"
        if duration > 0:
            desc += f" for {duration:.1f}s"
        return f"Moving: {desc}"

    def turn(self, degrees: float, speed_deg_per_sec: float = 45.0) -> str:
        """
        Turn the robot by an exact angle using closed-loop heading control.
        degrees: positive = left (counterclockwise), negative = right (clockwise).
        Polls the live heading from robot_state and stops when the target is reached,
        so errors do not accumulate across repeated turns.
        """
        degrees = float(max(-360.0, min(360.0, degrees)))
        speed_deg_per_sec = float(max(10.0, min(180.0, speed_deg_per_sec)))

        start_heading = self.state.heading_degrees()
        target_heading = start_heading + degrees

        wz = math.radians(speed_deg_per_sec) * (1.0 if degrees > 0 else -1.0)
        self.cmd_queue.put(Command("move", (0.0, 0.0, wz)))

        tolerance_deg = 1.5
        timeout = abs(degrees) / speed_deg_per_sec * 2.0  # safety cap
        deadline = time.time() + timeout

        while time.time() < deadline:
            current = self.state.heading_degrees()
            diff = (target_heading - current + 180.0) % 360.0 - 180.0
            if abs(diff) <= tolerance_deg:
                break
            time.sleep(0.02)

        self.cmd_queue.put(Command("stop"))
        return f"Turned {degrees:+.0f} degrees"

    def stop(self) -> str:
        """Stop the robot immediately."""
        self.cmd_queue.put(Command("stop"))
        return "Robot stopped."

    def get_state(self) -> str:
        """Return a human-readable description of the current robot state."""
        return self.state.to_description()
