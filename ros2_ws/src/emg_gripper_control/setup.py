from setuptools import find_packages, setup

package_name = 'emg_gripper_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='artempro',
    maintainer_email='artempro@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
	    'console_scripts': [
	        'emg_to_gripper = emg_gripper_control.emg_to_gripper_node:main',
	    ],
	},
)
