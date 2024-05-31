# SPDX-FileCopyrightText: NVIDIA CORPORATION & AFFILIATES
# Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
"""Live performance test for the Isaac ROS Hawk node (2 Hawk cameras)."""

import os

from ament_index_python.packages import get_package_share_directory

from isaac_ros_benchmark import NitrosMonitorUtility

import isaac_ros_hawk_nova_benchmark.hawk_benchmark_utility as hawk_benchmark_utility

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import LoadComposableNodes, Node

from ros2_benchmark import BenchmarkMode, ROS2BenchmarkConfig, ROS2BenchmarkTest

NITROS_MONITOR_UTILITY = NitrosMonitorUtility()


def launch_setup(container_prefix, container_sigterm_timeout):
    """Generate launch description for benchmarking Isaac ROS Hawk ESS depth graph."""
    result_load_list = []
    monitor_nodes = []
    benchmark_container = Node(
        name='benchmark_container',
        package='rclcpp_components',
        executable='component_container_mt',
        prefix=container_prefix,
        sigterm_timeout=container_sigterm_timeout,
        output='screen',
        arguments=[
            '--ros-args', '--log-level', 'info',
        ]
    )

    hawk_launch_include_dir = os.path.join(
        get_package_share_directory('isaac_ros_hawk_nova_benchmark'), 'scripts', 'include')

    # Front Hawk
    node_namespace = 'front'
    result_load_list.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource([hawk_launch_include_dir, '/hawk.include.py']),
        launch_arguments={
            'container_name': 'benchmark_container',
            'node_namespace': node_namespace,
            'hawk_placement': 'front',
            'create_correlated_timestamp_driver_node': 'True',
        }.items(),
    ))
    monitor_nodes.extend(hawk_benchmark_utility.create_hawk_monitors(
        NITROS_MONITOR_UTILITY,
        TestIsaacROSHawkEssDepthGraph.generate_namespace(),
        node_namespace))

    # Left Hawk
    node_namespace = 'left'
    result_load_list.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource([hawk_launch_include_dir, '/hawk.include.py']),
        launch_arguments={
            'container_name': 'benchmark_container',
            'node_namespace': node_namespace,
            'hawk_placement': 'left',
            'create_correlated_timestamp_driver_node': 'False',
        }.items(),
    ))
    monitor_nodes.extend(hawk_benchmark_utility.create_hawk_monitors(
        NITROS_MONITOR_UTILITY,
        TestIsaacROSHawkEssDepthGraph.generate_namespace(),
        node_namespace))

    load_benchmark_nodes = LoadComposableNodes(
        target_container='benchmark_container',
        composable_node_descriptions=monitor_nodes
    )

    return [benchmark_container, load_benchmark_nodes] + result_load_list


def generate_test_description():
    return TestIsaacROSHawkEssDepthGraph.generate_test_description_with_nsys(launch_setup)


class TestIsaacROSHawkEssDepthGraph(ROS2BenchmarkTest):
    """Performance test for the Isaac ROS Hawk node."""

    # Custom configurations
    config = ROS2BenchmarkConfig(
        benchmark_name='Isaac ROS Hawk Node (2 Hawk Cameras) Live Benchmark',
        benchmark_mode=BenchmarkMode.LIVE,
        benchmark_duration=5,
        test_iterations=5,
        collect_start_timestamps_from_monitors=True,
        pre_trial_run_wait_time_sec=10.0,
        monitor_info_list=[]
    )

    def test_benchmark(self):
        self.config.monitor_info_list = NITROS_MONITOR_UTILITY.get_monitor_info_list()
        self.run_benchmark()