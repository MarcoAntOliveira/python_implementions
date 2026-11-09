import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
import math

class FullAreaCoverageNode(Node):
    def __init__(self):
        super().__init__('full_area_coverage')
        
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )
        
        self.timer = self.create_timer(0.1, self.control_loop)
        
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.odom_ready = False
        
        # --- DEFINIÇÃO DA ÁREA (Grade de Varredura) ---
        # Vamos gerar uma lista de pontos (X, Y) em zigue-zague automaticamente
        # Exemplo: Área de 4 metros de comprimento por 2 metros de largura, espaçadas de 0.5m
        self.waypoints = self.generate_grid_waypoints(length=4.0, width=2.0, spacing=0.5)
        self.current_waypoint_index = 0
        
        # Tolerância para considerar que chegou em cada ponto da grade
        self.tolerance = 0.2

    def generate_grid_waypoints(self, length, width, spacing):
        waypoints = []
        y = 0.0
        going_forward = True
        
        while y <= width:
            if going_forward:
                waypoints.append((length, y))
                waypoints.append((length, y + spacing)) # Sobe para a próxima fileira
            else:
                waypoints.append((0.0, y))
                waypoints.append((0.0, y + spacing))
            
            y += spacing
            going_forward = not going_forward
            
        return waypoints

    def odom_callback(self, msg):
        pos = msg.pose.pose.position
        self.current_x = pos.x
        self.current_y = pos.y
        
        # Converte quaternion para Yaw
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)
        
        self.odom_ready = True

    def control_loop(self):
        if not self.odom_ready:
            return

        twist = Twist()

        # Verifica se já percorreu todos os pontos da área
        if self.current_waypoint_index >= len(self.waypoints):
            self.get_logger().info('Cobertura da área concluída com sucesso!', once=True)
            twist.linear.x = 0.0
            twist.angular.z = 0.0
            self.publisher_.publish(twist)
            return

        # Pega o alvo atual da grade
        target_x, target_y = self.waypoints[self.current_waypoint_index]

        # Calcula distância e ângulo até o alvo atual
        dx = target_x - self.current_x
        dy = target_y - self.current_y
        distance = math.sqrt(dx**2 + dy**2)
        angle_to_target = math.atan2(dy, dx)
        
        angle_error = angle_to_target - self.current_yaw
        angle_error = math.atan2(math.sin(angle_error), math.cos(angle_error))

        # Se chegou perto o suficiente do ponto atual, passa para o próximo
        if distance < self.tolerance:
            self.get_logger().info(f'Waypoint {self.current_waypoint_index} alcançado ({target_x}, {target_y})')
            self.current_waypoint_index += 1
        else:
            # Lógica proporcional simples para ir até o ponto
            if abs(angle_error) > 0.3:
                twist.linear.x = 0.0
                twist.angular.z = 0.4 * angle_error
            else:
                twist.linear.x = min(0.3, 0.5 * distance)
                twist.angular.z = 0.8 * angle_error

        self.publisher_.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = FullAreaCoverageNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publisher_.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()