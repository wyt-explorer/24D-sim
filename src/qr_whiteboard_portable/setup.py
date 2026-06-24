from setuptools import setup
import os
from glob import glob

package_name = 'qr_whiteboard_portable'

setup(
    name=package_name,
    version='0.0.0',
    packages=[],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'worlds'),
            glob('worlds/*')),
        (os.path.join('share', package_name, 'models/qr_whiteboard'),
            glob('models/qr_whiteboard/*.sdf') +
            glob('models/qr_whiteboard/model.config')),
        (os.path.join('share', package_name, 'models/qr_whiteboard/materials/scripts'),
            glob('models/qr_whiteboard/materials/scripts/*')),
        (os.path.join('share', package_name, 'models/qr_whiteboard/materials/textures'),
            glob('models/qr_whiteboard/materials/textures/*')),
        (os.path.join('share', package_name, 'models/qr_whiteboard/meshes'),
            glob('models/qr_whiteboard/meshes/*')),
        (os.path.join('share', package_name, 'hook'),
            glob('hook/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
)