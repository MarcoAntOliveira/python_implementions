import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

class SafeMotionPlannerNode(Node):
    def __init__(self):
        super().__init__('safe_motion_planner')
        
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan_front',
            self.scan_callback,
            10
        )
        
        self.timer = self.create_timer(0.1, self.control_loop)
        
        # Estados: 'FORWARD', 'REVERSE', 'TURN'
        self.state = 'FORWARD'
        self.state_counter = 0
        self.min_front_distance = 999.0

    def scan_callback(self, msg):
        ranges = msg.ranges
        if len(ranges) > 0:
            mid_index = len(ranges) // 2
            # Janela frontal central
            front_ranges = ranges[mid_index - 30 : mid_index + 30]
            valid_ranges = [r for r in front_ranges if r >= msg.range_min and r <= msg.range_max]
            
            if valid_ranges:
                self.min_front_distance = min(valid_ranges)
            else:
                self.min_front_distance = 999.0

    def control_loop(self):
        twist = Twist()

        # Máquina de estados para evitar travamentos
        if self.state == 'FORWARD':
            if self.min_front_distance < 0.4:  # Muito perto da parede (40 cm)
                self.get_logger().warn(f'Parede muito próxima ({self.min_front_distance:.2f}m)! Iniciando ré...')
                self.state = 'REVERSE'
                self.state_counter = 20  # Mantém a ré por 2 segundos (0.1s * 20)
            else:
                twist.linear.x = 0.2
                twist.angular.z = 0.0

        elif self.state == 'REVERSE':
            if self.state_counter > 0:
                twist.linear.x = -0.15  # Dá ré devagar
                twist.angular.z = 0.0
                self.state_counter -= 1
            else:
                # Terminou a ré, agora gira para buscar caminho livre
                self.get_logger().info('Girando para encontrar caminho livre...')
                self.state = 'TURN'
                self.state_counter = 25  # Gira por 2.5 segundos

        elif self.state == 'TURN':
            if self.state_counter > 0:
                twist.linear.x = 0.0
                twist.angular.z = 0.5  # Gira no próprio eixo
                self.state_counter -= 1
            else:
                # Volta a avançar e reavalia
                self.state = 'FORWARD'

        self.publisher_.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = SafeMotionPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Para o robô ao encerrar
        node.publisher_.publish(Twist())
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()