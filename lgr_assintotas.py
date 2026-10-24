import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# G(s) = K / [s(s+1)(s+2)]
polos = np.array([0, -1, -2], dtype=float)
zeros = np.array([], dtype=float)

n_p, n_z = len(polos), len(zeros)
n_assint = n_p - n_z

# Centroide e ângulos das assíntotas
sigma_a = (polos.sum() - zeros.sum()) / n_assint
angulos = [(2 * k + 1) * 180 / n_assint for k in range(n_assint)]  # 60, 180, 300
print(f"Centroide: {sigma_a}")
print(f"Ângulos: {[a if a <= 180 else a - 360 for a in angulos]}")

# Lugar das raízes: s^3 + 3s^2 + 2s + K = 0
Ks = np.concatenate([np.linspace(0, 1, 400), np.linspace(1, 100, 4000)])
raizes = np.array([np.roots([1, 3, 2, K]) for K in Ks])

# Ordena as raízes para manter continuidade de cada ramo
for i in range(1, len(raizes)):
    prev = raizes[i - 1]
    cur = list(raizes[i])
    ordenada = []
    for p in prev:
        j = int(np.argmin([abs(c - p) for c in cur]))
        ordenada.append(cur.pop(j))
    raizes[i] = ordenada

fig, ax = plt.subplots(figsize=(9, 7))

# Ramos do lugar das raízes
cores = ["tab:blue", "tab:green", "tab:red"]
for b in range(3):
    ax.plot(raizes[:, b].real, raizes[:, b].imag, color=cores[b], lw=2.2,
            label="Lugar das raízes" if b == 0 else None)

# Assíntotas
L = 6
for a in angulos:
    rad = np.deg2rad(a)
    x = [sigma_a, sigma_a + L * np.cos(rad)]
    y = [0, L * np.sin(rad)]
    ax.plot(x, y, "k--", lw=1.3, label="Assíntotas" if a == angulos[0] else None)

# Polos, centroide
ax.plot(polos.real, np.zeros_like(polos), "x", color="black", ms=12, mew=3, label="Polos de MA")
ax.plot(sigma_a, 0, "o", color="orange", ms=9, mec="black", label=r"Centroide $\sigma_a=-1$")

# Ângulos anotados
ax.annotate("60°", (sigma_a + 1.3, 0.35), fontsize=12)
ax.annotate("-60°", (sigma_a + 1.3, -0.65), fontsize=12)
ax.annotate("180°", (sigma_a - 1.3, 0.15), fontsize=12)

ax.axhline(0, color="gray", lw=0.8)
ax.axvline(0, color="gray", lw=0.8)
ax.set_xlim(-4, 3)
ax.set_ylim(-4, 4)
ax.set_xlabel("Eixo real")
ax.set_ylabel("Eixo imaginário")
ax.set_title(r"Lugar das raízes de $G(s)=\dfrac{K}{s(s+1)(s+2)}$ com assíntotas")
ax.grid(alpha=0.3)
ax.legend(loc="upper right")
ax.set_aspect("equal")

plt.tight_layout()
plt.savefig("lgr_assintotas.png", dpi=150)
print("Salvo em lgr_assintotas.png")