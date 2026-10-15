import rclpy
from std_msgs.msg import Float32


def pid_controller(setpoint, pv, kp, ki, kd, previous_error, integral, dt):
    error = setpoint - pv
    integral += error * dt
    derivative = (error - previous_error) / dt
    control = kp * error + ki * integral + kd * derivative
    return control, error, integral


def main():
    rclpy.init()
    node = rclpy.create_node('pid_test')

    pub_control = node.create_publisher(Float32, '/pid/control', 10)
    pub_setpoint = node.create_publisher(Float32, '/pid/setpoint', 10)
    pub_pv = node.create_publisher(Float32, '/pid/pv', 10)

    setpoint = 100.0
    pv = 0.0
    kp, ki, kd = 1.0, 0.1, 0.05
    previous_error = 0.0
    integral = 0.0
    dt = 0.1

    def timer_callback():
        nonlocal pv, previous_error, integral

        control, error, integral = pid_controller(
        setpoint, pv, kp, ki, kd, previous_error, integral, dt)
        pv += control * dt  # planta simplificada
        previous_error = error

        pub_control.publish(Float32(data=float(control)))
        pub_setpoint.publish(Float32(data=float(setpoint)))
        pub_pv.publish(Float32(data=float(pv)))

    node.create_timer(dt, timer_callback)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()