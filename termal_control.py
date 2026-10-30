import random
import rclpy
from std_msgs.msg import Float32
import sympy as sp

kp, ki, kd, s = sp.symbols('kp ki kd s')
class PID:
    def __init__(self, kp, ki, kd, out_min, out_max):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self.integral = 0.0      # já em unidades de saída (W)
        self.prev_pv = None


    

    def update(self, setpoint, pv, dt):
        error = setpoint - pv

        # derivada sobre a medição (evita "kick" quando o setpoint muda)
        d = 0.0 if self.prev_pv is None else -(pv - self.prev_pv) / dt
        self.prev_pv = pv

        i_candidate = self.integral + self.ki * error * dt
        u = self.kp * error + i_candidate + self.kd * d

        # anti-windup: só integra se não estiver saturado,
        # ou se o erro estiver puxando a saída de volta para a faixa
        if self.out_min < u < self.out_max:
            self.integral = i_candidate
        elif (u >= self.out_max and error < 0) or (u <= self.out_min and error > 0):
            self.integral = i_candidate

        return max(self.out_min, min(self.out_max, u))


class ThermalPlant:
    def __init__(self, t_amb=25.0, k=0.5, tau=60.0):
        self.t_amb, self.k, self.tau = t_amb, k, tau
        self.temp = t_amb

    def step(self, power, dt):
        dT = (-(self.temp - self.t_amb) + self.k * power) / self.tau
        self.temp += dT * dt
        return self.temp


def main():
    rclpy.init()
    node = rclpy.create_node('pid_thermal')
    node.declare_parameter('setpoint', 60.0)

    pub_temp1 = node.create_publisher(Float32, '/thermal/temperature1', 10)
    pub_temp2 = node.create_publisher(Float32, '/thermal/temperature2', 10)
    pub_sp = node.create_publisher(Float32, '/thermal/setpoint', 10)
    pub_power1 = node.create_publisher(Float32, '/thermal/power1', 10)
    pub_power2 = node.create_publisher(Float32, '/thermal/power2', 10)

    dt = 0.1
    p_max = 100.0  # W (com K=0.5 => temperatura máxima = 25 + 50 = 75 °C)
    
    plant1 = ThermalPlant(t_amb=25.0, k=0.5, tau=60.0)
    plant2 = ThermalPlant(t_amb=25.0, k=0.5, tau=60.0)
    pid1 = PID(kp=8.0, ki=0.15, kd=0.0, out_min=0.0, out_max=p_max)
    pid2 = PID(kp=20.0, ki=0.4, kd=0.0, out_min=0.0, out_max=p_max)   # ganhos diferentes

    def timer_callback():
        setpoint = node.get_parameter('setpoint').value

        m1 = plant1.temp + random.gauss(0.0, 0.05)
        m2 = plant2.temp + random.gauss(0.0, 0.05)

        p1 = pid1.update(setpoint, m1, dt)
        p2 = pid2.update(setpoint, m2, dt)

        plant1.step(p1, dt)
        plant2.step(p2, dt)

        pub_temp1.publish(Float32(data=float(m1)))
        pub_temp2.publish(Float32(data=float(m2)))
        pub_power1.publish(Float32(data=float(p1)))
        pub_power2.publish(Float32(data=float(p2)))
        pub_sp.publish(Float32(data=float(setpoint)))

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