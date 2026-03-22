"""
Simulation node — kinematic mobile robot simulation.

In headless mode (default) no external library is required beyond pyarrow.
Set PYBULLET_GUI=1 to open a 3D PyBullet visualisation window.

Inputs:
  tick         : timer        — physics step trigger (50 ms)
  velocity_cmd : float32[3]   — [vx, vy, wz] in robot frame (m/s, m/s, rad/s)
  stop_cmd     : int8[1]      — halt all motion

Outputs:
  robot_state  : float32[10]  — [px,py,pz, ox,oy,oz,ow, vx,vy,vz]
"""

import math
import os

import pyarrow as pa
from dora import Node

DT = 0.05
MAX_LINEAR = 2.0
MAX_ANGULAR = 3.14


def _euler_to_quaternion(yaw: float) -> tuple:
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return (0.0, 0.0, sy, cy)  # x, y, z, w


def _init_pybullet(gui: bool):
    import pybullet as p
    import pybullet_data
    client = p.connect(p.GUI if gui else p.DIRECT)
    p.setAdditionalSearchPath(pybullet_data.getDataPath(), physicsClientId=client)
    p.setGravity(0, 0, -9.81, physicsClientId=client)
    p.loadURDF("plane.urdf", physicsClientId=client)
    robot_id = p.loadURDF("r2d2.urdf", [0, 0, 0.5], physicsClientId=client)
    return p, client, robot_id


def main() -> None:
    node = Node()

    gui_mode = os.environ.get("PYBULLET_GUI", "0") == "1"
    pb = client = robot_id = None

    if gui_mode:
        pb, client, robot_id = _init_pybullet(gui=True)

    x, y, z = 0.0, 0.0, 0.25
    yaw = 0.0
    vx_cmd = vy_cmd = wz_cmd = 0.0

    def update_visual() -> None:
        if pb is None:
            return
        quat = _euler_to_quaternion(yaw)
        pb.resetBasePositionAndOrientation(
            robot_id, [x, y, z], quat, physicsClientId=client
        )

    for event in node:
        if event["type"] == "STOP":
            break

        if event["type"] != "INPUT":
            continue

        input_id = event["id"]

        if input_id == "velocity_cmd":
            vals = event["value"].to_pylist()
            vx_cmd = max(-MAX_LINEAR, min(MAX_LINEAR, float(vals[0])))
            vy_cmd = max(-MAX_LINEAR, min(MAX_LINEAR, float(vals[1])))
            wz_cmd = max(-MAX_ANGULAR, min(MAX_ANGULAR, float(vals[2])))

        elif input_id == "stop_cmd":
            vx_cmd = vy_cmd = wz_cmd = 0.0

        elif input_id == "tick":
            world_vx = vx_cmd * math.cos(yaw) - vy_cmd * math.sin(yaw)
            world_vy = vx_cmd * math.sin(yaw) + vy_cmd * math.cos(yaw)
            x += world_vx * DT
            y += world_vy * DT
            yaw += wz_cmd * DT

            update_visual()

            quat = _euler_to_quaternion(yaw)
            state = [x, y, z, *quat, world_vx, world_vy, 0.0]
            node.send_output("robot_state", pa.array(state, type=pa.float32()))

    if pb is not None:
        pb.disconnect(physicsClientId=client)


if __name__ == "__main__":
    main()
