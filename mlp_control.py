import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from visualization_msgs.msg import Marker
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped

from mlp_control import net, pd, UMAX   # rede já treinada + professor


class ControlViz(Node):
    def __init__(self):
        super().__init__("control_viz")
        self.dt, self.target = 0.05, 5.0
        self.s = {"nn": [0.0, 0.0], "pd": [0.0, 0.0]}   # [z, vz]

        self.pub = {}
        for k in ("nn", "pd"):
            self.pub[f"z_{k}"] = self.create_publisher(Float64, f"/ctrl/z_{k}", 10)
            self.pub[f"u_{k}"] = self.create_publisher(Float64, f"/ctrl/u_{k}", 10)
        self.pub_tgt = self.create_publisher(Float64, "/ctrl/target", 10)
        self.pub_mk = self.create_publisher(Marker, "/ctrl/markers", 10)
        self.pub_path = self.create_publisher(Path, "/ctrl/path_nn", 10)

        self.path = Path()
        self.path.header.frame_id = "world"
        self.create_timer(self.dt, self.tick)

    def policy(self, k, e, v):
        if k == "pd":
            return float(pd(e, v))
        return float(net.forward(np.array([[e / 10], [v / 5]]))[0, 0] * UMAX)

    def tick(self):
        now = self.get_clock().now().to_msg()
        for idx, k in enumerate(("nn", "pd")):
            z, vz = self.s[k]
            u = self.policy(k, self.target - z, vz)
            vz += u * self.dt
            z += vz * self.dt
            self.s[k] = [z, vz]

            self.pub[f"z_{k}"].publish(Float64(data=z))
            self.pub[f"u_{k}"].publish(Float64(data=u))

            # esfera no RViz: NN em x=0 (azul), PD em x=1 (vermelho)
            m = Marker()
            m.header.frame_id, m.header.stamp = "world", now
            m.ns, m.id = "ctrl", idx
            m.type, m.action = Marker.SPHERE, Marker.ADD
            m.pose.position.x, m.pose.position.z = float(idx), float(z)
            m.scale.x = m.scale.y = m.scale.z = 0.3
            m.color.a = 1.0
            m.color.b, m.color.r = (1.0, 0.0) if k == "nn" else (0.0, 1.0)
            self.pub_mk.publish(m)

        self.pub_tgt.publish(Float64(data=self.target))

        # rastro da NN
        p = PoseStamped()
        p.header.frame_id, p.header.stamp = "world", now
        p.pose.position.z = float(self.s["nn"][0])
        self.path.poses.append(p)
        self.path.header.stamp = now
        self.pub_path.publish(self.path)


def main():
    rclpy.init()
    rclpy.spin(ControlViz())

if __name__ == "__main__":
    main()