from setuptools import setup
import os
from glob import glob

package_name = "as2_qr_mission"

setup(
    name=package_name,
    version="0.0.0",
    packages=[package_name],
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.py"),
        ),
        (
            os.path.join("share", package_name, "worlds"),
            glob("worlds/*.sdf"),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    entry_points={
    "console_scripts": [
        "mission = as2_qr_mission.mission_node:main",
        "laser = as2_qr_mission.laser_node:main",
        "qr_detector = as2_qr_mission.qr_detector_node:main",
        ],
    },
)