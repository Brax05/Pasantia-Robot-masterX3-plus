cmake_minimum_required(VERSION 3.0.2)
project(yahboomcar_llm)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  geometry_msgs
  sensor_msgs
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/llm_bridge_node.py
  scripts/vision_pipeline.py
  scripts/action_parser.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)
