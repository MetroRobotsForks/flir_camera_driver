# -----------------------------------------------------------------------------
# Copyright 2025 Bernd Pfrommer <bernd.pfrommer@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#


#
# Example file for two Blackfly S GigE cameras that are *externally triggered*
# and have a working PTP (IEEE1588) setup, i.e
# you must provide an external hardware synchronization pulse to both cameras,
# and the cameras must be connected to a PTP network.
#


from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument as LaunchArg
from launch.actions import OpaqueFunction
from launch.substitutions import LaunchConfiguration as LaunchConfig
from launch.substitutions import PathJoinSubstitution as PJoin
from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from launch_ros.substitutions import FindPackageShare

camera_list = {
    'cam0': '20255396',
    'cam1': '20255407',
}


cam_parameters = {
    'debug': False,
    'quiet': True,
    'buffer_queue_size': 1,
    'compute_brightness': False,
    'exposure_auto': 'Continuous',
    'trigger_mode': 'On',
    'gain_auto': 'Continuous',
    'trigger_source': 'Line3',
    'trigger_selector': 'FrameStart',
    'trigger_overlap': 'ReadOut',
    'trigger_activation': 'RisingEdge',
    'balance_white_auto': 'Continuous',
    # enable PTP (IEEE1588) at the camera level
    'gev_ieee_1588': True,
    'gev_ieee_1588_mode': 'Auto', # 'SlaveOnly',  #'Auto',
    'use_ieee_1588' : True, # use PTP to compute time stamps
    # You must enable chunk mode and the chunk frame_id
    'chunk_mode_active': True,
    'chunk_selector_frame_id': 'FrameID',  # needed to detect dropped frames
    'chunk_enable_frame_id': True,
    # Since we are using PTP, the timestamp *must* be enabled!
    'chunk_selector_timestamp': 'Timestamp',
    'chunk_enable_timestamp': True,
    # Switch these off for testing since we are running auto-exposure
    # These should usually be switched on for the metadata messages
    'chunk_selector_exposure_time': 'ExposureTime',
    'chunk_enable_exposure_time': False,
    'chunk_selector_gain': 'Gain',
    'chunk_enable_gain': False,
}


def make_parameters(context):
    """Launch synchronized camera driver node."""
    pd = LaunchConfig('camera_parameter_directory')
    calib_url = 'file://' + LaunchConfig('calibration_directory').perform(context) + '/'

    driver_parameters = {
        'cameras': list(camera_list.keys()),
        'use_ieee_1588': True,  # tell synchronized driver to actually use PTP
    }

    # generate camera parameters
    cam_parameters['parameter_file'] = PJoin([pd, 'blackfly_s.yaml'])
    for cam, serial in camera_list.items():
        cam_params = {cam + '.' + k: v for k, v in cam_parameters.items()}
        cam_params[cam + '.serial_number'] = serial
        cam_params[cam + '.camerainfo_url'] = calib_url + serial + '.yaml'
        cam_params[cam + '.frame_id'] = cam
        driver_parameters.update(cam_params)  # insert into main parameter list
    return driver_parameters


def launch_setup(context, *args, **kwargs):
    container = ComposableNodeContainer(
        name='cam_sync_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            ComposableNode(
                package='spinnaker_synchronized_camera_driver',
                plugin='spinnaker_synchronized_camera_driver::SynchronizedCameraDriver',
                name='cam_sync',
                parameters=[make_parameters(context)],
                extra_arguments=[{'use_intra_process_comms': True}],
            ),
        ],
        output='screen',
    )  # end of container
    return [container]


def generate_launch_description():
    return LaunchDescription(
        [
            LaunchArg(
                'camera_parameter_directory',
                default_value=PJoin([FindPackageShare('spinnaker_camera_driver'), 'config']),
                description='root directory for camera parameter definitions',
            ),
            LaunchArg(
                'calibration_directory',
                default_value=['camera_calibrations'],
                description='root directory for camera calibration files',
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
