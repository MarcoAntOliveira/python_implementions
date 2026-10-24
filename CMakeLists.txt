cmake_minimum_required(VERSION 3.16)
project(cpp_test)

set(CMAKE_CXX_STANDARD 17)

find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(yaets REQUIRED)

set(link_dependencies
  rclcpp::rclcpp
  yaets::yaets
  ${std_msgs_TARGETS}

)

add_executable(node rtos.cpp)
# ament_target_dependencies(node my_px4_msg)
target_link_libraries(node ${link_dependencies})

add_executable(node2 rtos_linux.cpp)
# ament_target_dependencies(node my_px4_msg)
target_link_libraries(node2 ${link_dependencies})