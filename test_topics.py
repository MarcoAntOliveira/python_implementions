#!/usr/bin/env python3
"""Testa se os topicos da bridge Gazebo -> ROS 2 (Tugbot) estao chegando.

Uso:
  python3 test_topics.py              # escuta 10 s
  python3 test_topics.py -t 15        # escuta 15 s
  python3 test_topics.py --move       # tambem manda cmd_vel e confere se /odom mudou
"""
import argparse
import math
import time

import rclpy
from geometry_msgs.msg import Pose, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rosgraph_msgs.msg import Clock
from sensor_msgs.msg import (BatteryState, CameraInfo, Image, Imu, JointState,
                             LaserScan, PointCloud2)
from tf2_msgs.msg import TFMessage

TOPICS = {
    "/clock": Clock,
    "/odom": Odometry,
    "/tf": TFMessage,
    "/tugbot/pose": TFMessage,
    "/tugbot/joint_states": JointState,
    "/tugbot/battery_state": BatteryState,
    "/imu": Imu,
    "/scan_front": LaserScan,
    "/scan_back": LaserScan,
    "/scan_omni": LaserScan,
    "/scan_front/points": PointCloud2,
    "/scan_back/points": PointCloud2,
    "/scan_omni/points": PointCloud2,
    "/gripper/contact_scan": LaserScan,
    "/gripper/contact_scan/points": PointCloud2,
    "/camera_front/color/image": Image,
    "/camera_front/color/camera_info": CameraInfo,
    "/camera_front/depth/image": Image,
    "/camera_front/depth/camera_info": CameraInfo,
    "/camera_front/depth/points": PointCloud2,
    "/camera_back/color/image": Image,
    "/camera_back/color/camera_info": CameraInfo,
    "/camera_back/depth/image": Image,
    "/camera_back/depth/camera_info": CameraInfo,
    "/camera_back/depth/points": PointCloud2,
    "/pallet_box/pose": Pose,
    "/pallet_box_0/pose": Pose,
    "/pallet_box_mobile/pose": Pose,
    "/pallet_box_mobile_0/pose": Pose,
    "/pallet_box_mobile_1/pose": Pose,
}


class TopicTester(Node):
    def __init__(self):
        super().__init__("topic_tester")
        self.count = {t: 0 for t in TOPICS}
        self.first_odom = None
        self.last_odom = None
        for topic, msg_type in TOPICS.items():
            # sensor_data = BEST_EFFORT, recebe de publishers reliable ou best effort
            self.create_subscription(
                msg_type, topic, self._make_cb(topic), qos_profile_sensor_data)
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)

    def _make_cb(self, topic):
        def cb(msg):
            self.count[topic] += 1
            if topic == "/odom":
                p = msg.pose.pose.position
                if self.first_odom is None:
                    self.first_odom = (p.x, p.y)
                self.last_odom = (p.x, p.y)
        return cb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--time", type=float, default=10.0, help="segundos de escuta")
    ap.add_argument("--move", action="store_true", help="publica cmd_vel e confere /odom")
    args = ap.parse_args()

    rclpy.init()
    node = TopicTester()

    twist = Twist()
    twist.linear.x = 0.3
    t0 = time.time()
    last_pub = 0.0
    while time.time() - t0 < args.time:
        rclpy.spin_once(node, timeout_sec=0.05)
        if args.move and time.time() - last_pub > 0.1:
            node.cmd_pub.publish(twist)
            last_pub = time.time()

    if args.move:
        node.cmd_pub.publish(Twist())  # para o robo

    elapsed = time.time() - t0
    print(f"\n{'TOPICO':<36}{'STATUS':<10}{'MSGS':>7}{'Hz':>8}")
    print("-" * 61)
    ok = 0
    for topic in TOPICS:
        n = node.count[topic]
        status = "OK" if n > 0 else "SEM DADOS"
        ok += n > 0
        print(f"{topic:<36}{status:<10}{n:>7}{n / elapsed:>8.1f}")
    print("-" * 61)
    print(f"{ok}/{len(TOPICS)} topicos com dados em {elapsed:.0f} s")

    if args.move:
        if node.first_odom and node.last_odom:
            d = math.dist(node.first_odom, node.last_odom)
            print(f"\nTeste cmd_vel -> odom: deslocamento de {d:.2f} m",
                  "(OK)" if d > 0.05 else "(robo nao se moveu: confira /cmd_vel e /model/tugbot/enable)")
        else:
            print("\nTeste cmd_vel -> odom: sem dados de /odom")

    print("\nObs: poses de pallets estaticos so publicam quando mudam; "
          "SEM DADOS neles e normal. Cameras podem exigir mais tempo (-t 20).")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()