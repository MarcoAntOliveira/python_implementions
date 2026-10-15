import random
import rclpy
from rcl_interfaces.msg import SetParametersResult
from std_msgs.msg import Float32
from termal_control import PID, ThermalPlant



def main():
    rclpy.init()
    node = rclpy.create_node('pid_tuner')
    node.declare_parameter('setpoint', 60.0)
    node.declare_parameter('kp', 8.0)
    node.declare_parameter('ki', 0.15)
    node.declare_parameter('kd', 0.0)
    node.declare_parameter('noise', 0.05)
    node.declare_parameter('reset', False)

    pub_temp = node.create_publisher(Float32, '/thermal/temperature', 10)
    pub_sp = node.create_publisher(Float32, '/thermal/setpoint', 10)
    pub_power = node.create_publisher(Float32, '/thermal/power', 10)
    pub_err = node.create_publisher(Float32, '/thermal/error', 10)

    dt = 0.1
    plant = ThermalPlant(t_amb=25.0, k=0.5, tau=60.0)
    pid = PID(kp=8.0, ki=0.15, kd=0.0, out_min=0.0, out_max=100.0)

    def on_params(params):
        for p in params:
            if p.name in ('kp', 'ki', 'kd'):
                setattr(pid, p.name, float(p.value))
            elif p.name == 'reset' and p.value:
                plant.temp = plant.t_amb
                pid.integral = 0.0
                pid.prev_pv = None
        return SetParametersResult(successful=True)

    node.add_on_set_parameters_callback(on_params)

    def timer_callback():
        sp = node.get_parameter('setpoint').value
        noise = node.get_parameter('noise').value
        measured = plant.temp + random.gauss(0.0, noise)
        power = pid.update(sp, measured, dt)
        plant.step(power, dt)

        pub_temp.publish(Float32(data=float(measured)))
        pub_sp.publish(Float32(data=float(sp)))
        pub_power.publish(Float32(data=float(power)))
        pub_err.publish(Float32(data=float(sp - measured)))

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