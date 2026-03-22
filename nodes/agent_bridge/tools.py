import time
from dataclasses import dataclass, field
from typing import Tuple
import math


@dataclass
class RobotState:
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    orientation: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0)
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    last_updated: float = field(default_factory=time.time)

    def update_from_flat(self, data: list) -> None:
        """Update state from 10-element flat array [px,py,pz,ox,oy,oz,ow,vx,vy,vz]."""
        self.position = (float(data[0]), float(data[1]), float(data[2]))
        self.orientation = (float(data[3]), float(data[4]), float(data[5]), float(data[6]))
        self.velocity = (float(data[7]), float(data[8]), float(data[9]))
        self.last_updated = time.time()

    def heading_degrees(self) -> float:
        """Extract yaw angle in degrees from orientation quaternion."""
        ox, oy, oz, ow = self.orientation
        siny_cosp = 2.0 * (ow * oz + ox * oy)
        cosy_cosp = 1.0 - 2.0 * (oy * oy + oz * oz)
        return math.degrees(math.atan2(siny_cosp, cosy_cosp))

    def to_description(self) -> str:
        px, py, pz = self.position
        vx, vy, vz = self.velocity
        heading = self.heading_degrees()
        return (
            f"Position: ({px:.2f}, {py:.2f}, {pz:.2f}) m, "
            f"Heading: {heading:.1f} deg, "
            f"Velocity: ({vx:.2f}, {vy:.2f}) m/s"
        )


@dataclass
class RobotCommand:
    command_type: str = "none"
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def reset(self) -> None:
        self.command_type = "none"
        self.velocity = (0.0, 0.0, 0.0)


class RobotTools:
    """
    Pure Python robot tool implementations.
    Writes commands into a shared RobotCommand and reads from a shared RobotState.
    """

    def __init__(self, state: RobotState, command: RobotCommand) -> None:
        self.state = state
        self.command = command

    def move(self, vx: float, vy: float = 0.0, wz: float = 0.0) -> str:
        """Move the robot. vx=forward (m/s), vy=lateral (m/s), wz=turn (rad/s)."""
        vx = float(max(-2.0, min(2.0, vx)))
        vy = float(max(-2.0, min(2.0, vy)))
        wz = float(max(-3.14, min(3.14, wz)))
        self.command.command_type = "move"
        self.command.velocity = (vx, vy, wz)
        parts = []
        if abs(vx) > 0.01:
            parts.append(f"vx={vx:.2f} m/s")
        if abs(vy) > 0.01:
            parts.append(f"vy={vy:.2f} m/s")
        if abs(wz) > 0.01:
            parts.append(f"wz={wz:.2f} rad/s")
        desc = ", ".join(parts) if parts else "stationary"
        return f"Moving: {desc}"

    def stop(self) -> str:
        """Stop the robot immediately."""
        self.command.command_type = "stop"
        self.command.velocity = (0.0, 0.0, 0.0)
        return "Robot stopped."

    def get_state(self) -> str:
        """Return a human-readable description of the current robot state."""
        return self.state.to_description()
