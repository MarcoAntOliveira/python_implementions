import control as ct
import matplotlib.pyplot as plt

# 1. Defina a função de transferência em malha aberta: G(s)H(s) = (s + 3) / (s^3 + 3s^2 + 5s + 1)
# for k in range(1, 17):
#     sys = ct.TransferFunction([k], [1, 8, k])
#     # 2. Calcule e plote o Lugar das Raízes
#     raizes, ganhos = ct.root_locus(sys, plot=True)

sys = ct.TransferFunction([0,0,1,1], [1,5,6,0])
raizes, ganhos = ct.root_locus(sys, plot=True)

# 3. Exiba o gráfico
plt.title("Lugar Geométrico das Raízes (LGR)")
plt.show()
