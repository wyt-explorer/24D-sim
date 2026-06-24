"""QR mission using Aerostack2 x500 in the existing QR whiteboard world.

This keeps the Aerostack2 x500 model and AS2 Gazebo simulation launcher.
The mission directly commands Gazebo velocity topics because manual
/model/drone0/cmd_vel control has been verified to work.
"""

import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_qr = get_package_share_directory("as2_qr_mission")
    pkg_qr_board = get_package_share_directory("qr_whiteboard_portable")
    pkg_gz_assets = get_package_share_directory("as2_gazebo_assets")

    simulation_config_file = os.path.join(
        pkg_qr,
        "config",
        "qr_as2_world.yaml",
    )

    gz_resource_path = ":".join([
        os.path.join(pkg_qr_board, "worlds"),
        os.path.join(pkg_qr_board, "models"),
        os.path.join(pkg_gz_assets, "worlds"),
        os.path.join(pkg_gz_assets, "models"),
    ])

    old_ign = os.environ.get("IGN_GAZEBO_RESOURCE_PATH", "")
    old_gz = os.environ.get("GZ_SIM_RESOURCE_PATH", "")

    combined_ign = gz_resource_path + (":" + old_ign if old_ign else "")
    combined_gz = gz_resource_path + (":" + old_gz if old_gz else "")

    gazebo_simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gz_assets, "launch", "launch_simulation.py")
        ),
        launch_arguments={
            "simulation_config_file": simulation_config_file,
            "run_on_start": "true",
            "headless": "false",
        }.items(),
    )

    control_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="drone0_direct_control_bridge",
        output="screen",
        arguments=[
            "/model/drone0/cmd_vel@geometry_msgs/msg/Twist]ignition.msgs.Twist",
            "/model/drone0/velocity_controller/enable@std_msgs/msg/Bool]ignition.msgs.Boolean",
        ],
    )

    pose_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="drone0_direct_pose_bridge",
        output="screen",
        arguments=[
            "/model/drone0/pose@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
        ],
    )

    laser_node = Node(
        package="as2_qr_mission",
        executable="laser",
        name="laser_node",
        output="screen",
        parameters=[
            {"use_sim_time": True},
        ],
    )

    mission_node = Node(
        package="as2_qr_mission",
        executable="mission",
        name="qr_mission",
        output="screen",
        parameters=[
            {"use_sim_time": True},
        ],
    )

    return LaunchDescription([
        SetEnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", combined_ign),
        SetEnvironmentVariable("GZ_SIM_RESOURCE_PATH", combined_gz),

        gazebo_simulation,

        TimerAction(period=8.0, actions=[
            control_bridge,
            pose_bridge,
            laser_node,
        ]),

        TimerAction(period=12.0, actions=[
            mission_node,
        ]),
    ])