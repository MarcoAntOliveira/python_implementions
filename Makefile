
bridge:
	ros2 run ros_gz_bridge parameter_bridge --ros-args -p config_file:=/home/marcos/projects/python_implementations/tugbot_bridge.yaml

log:	
	ulog2csv log.ulg -m /cmd_vel.x