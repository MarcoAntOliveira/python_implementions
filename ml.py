import numpy as np


class LinearRegression:
    def __init__(self, lr=0.01, epochs=1000):
        self.lr = lr
        self.epochs = epochs
        self.weights = None
        self.bias = None


    def fit(self, X, y):
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0


        for _ in range(self.epochs):
            y_pred = X @ self.weights + self.bias
            error = y_pred - y


            # Gradients
            dw = (2/n_samples) * X.T @ error
            db = (2/n_samples) * np.sum(error)


            # Update
            self.weights -= self.lr * dw
            self.bias   -= self.lr * db
    def predict(self, X):
        return X @ self.weights + self.bias



def sigmoid(z):       return 1 / (1 + np.exp(-z))
def sigmoid_deriv(z): return sigmoid(z) * (1 - sigmoid(z))


class NeuralNetwork:
    def __init__(self, layer_sizes):
        self.weights = []
        self.biases  = []
        for i in range(len(layer_sizes)-1):
            W = np.random.randn(layer_sizes[i+1], layer_sizes[i]) * 0.01
            b = np.zeros((layer_sizes[i+1], 1))
            self.weights.append(W)
            self.biases.append(b)


    def forward(self, X):
        self.zs, self.activations = [], [X]
        A = X
        for W, b in zip(self.weights, self.biases):
            Z = W @ A + b
            A = sigmoid(Z)
            self.zs.append(Z)
            self.activations.append(A)
        return A


    def backward(self, y, lr=0.01):
        m = y.shape[1]
        delta = self.activations[-1] - y  # output layer error
        for i in reversed(range(len(self.weights))):
            dW = (delta @ self.activations[i].T) / m
            db = np.sum(delta, axis=1, keepdims=True) / m
            if i > 0:
                delta = (self.weights[i].T @ delta) * sigmoid_deriv(self.zs[i-1])
            self.weights[i] -= lr * dW
            self.biases[i]  -= lr * db
       # ---------- ACRESCENTADO ----------

    # 1. train(X, y, epochs, lr)

    # O que faz: repete forward + backward várias vezes e imprime a perda de tempos em tempos.
    # Por que: a sua classe só tinha um passo de aprendizado (backward). Uma rede só aprende 
    # depois de milhares de passos, então alguém precisa ficar chamando o laço. Antes eu deixava
    # isso solto fora da classe; agora fica encapsulado.
    def train(self, X, y, epochs=3000, lr=0.5, verbose=True):
        for ep in range(epochs):
            A = self.forward(X)
            self.backward(y, lr)
            if verbose and ep % 500 == 0:
                print(ep, "loss:", np.mean((A - y) ** 2))
    # 2. predict(X)

    # O que faz: roda o forward e devolve a classe vencedora (argmax) e a confiança (max).
    # Por que: o forward devolve 10 probabilidades. Para usar no ROS você precisa de “qual classe é” e 
    # “quão certa a rede está”. A confiança serve pra descartar leituras duvidosas 
    # (por exemplo, só agir se conf > 0.8).
    def predict(self, X):
        A = self.forward(X)
        return A.argmax(axis=0), A.max(axis=0)      # classe e confiança

    def save(self, path):
        np.savez(path, *self.weights, *self.biases, n=len(self.weights))
        
    @classmethod
    def load(cls, path):
        d = np.load(path)
        n = int(d["n"])
        net = cls.__new__(cls)
        net.weights = [d[f"arr_{i}"] for i in range(n)]
        net.biases  = [d[f"arr_{i}"] for i in range(n, 2 * n)]
        return net

class KMeans:
    def __init__(self, k=3, max_iters=100, n_init=10, tol=1e-4, seed=None):
        self.k = k
        self.max_iters = max_iters
        self.n_init = n_init
        self.tol = tol
        self.rng = np.random.default_rng(seed)

    # ---------- helpers ----------
    @staticmethod
    def _sq_dists(X, C):
        # (n, k): distância² de cada ponto a cada centroide, vetorizado
        return ((X[:, None, :] - C[None, :, :]) ** 2).sum(axis=2)

    def _init_plus_plus(self, X):
        n = len(X)
        C = [X[self.rng.integers(n)]]
        for _ in range(1, self.k):
            d2 = self._sq_dists(X, np.array(C)).min(axis=1)
            total = d2.sum()
            if total == 0:                       # todos os pontos iguais aos centroides
                C.append(X[self.rng.integers(n)])
                continue
            C.append(X[self.rng.choice(n, p=d2 / total)])
        return np.array(C)

    def _run_once(self, X):
        C = self._init_plus_plus(X)
        for _ in range(self.max_iters):
            labels = self._sq_dists(X, C).argmin(axis=1)

            new_C = C.copy()
            for j in range(self.k):
                members = X[labels == j]
                if len(members):                 # cluster vazio: mantém o centroide antigo
                    new_C[j] = members.mean(axis=0)

            shift = np.linalg.norm(new_C - C)
            C = new_C
            if shift < self.tol:
                break

        d2 = self._sq_dists(X, C)
        labels = d2.argmin(axis=1)
        inertia = d2[np.arange(len(X)), labels].sum()
        return C, labels, inertia

    # ---------- API ----------
    def fit(self, X):
        X = np.asarray(X, dtype=float)
        if self.k > len(X):
            raise ValueError("k não pode ser maior que o número de amostras")

        best = None
        for _ in range(self.n_init):
            result = self._run_once(X)
            if best is None or result[2] < best[2]:
                best = result
        self.centroids, self.labels, self.inertia_ = best
        return self

    def predict(self, X):
        return self._sq_dists(np.asarray(X, dtype=float), self.centroids).argmin(axis=1)
class NaiveBayes:
    def fit(self, X, y):
        self.classes = np.unique(y)
        self.priors  = {}
        self.means   = {}
        self.vars    = {}


        for c in self.classes:
            X_c = X[y == c]
            self.priors[c] = len(X_c) / len(X)
            self.means[c]  = X_c.mean(axis=0)
            self.vars[c]   = X_c.var(axis=0)


    def _gaussian_log_pdf(self, x, mean, var):
        # log of Gaussian probability density function
        return -0.5 * np.log(2 * np.pi * var) - ((x - mean)**2 / (2 * var))


    def predict(self, X):
      preds = []
      for x in X:
            log_probs = {}
            for c in self.classes:
                log_prior = np.log(self.priors[c])
                log_likelihood = np.sum(
                    self._gaussian_log_pdf(x, self.means[c], self.vars[c])
                )
                log_probs[c] = log_prior + log_likelihood
            preds.append(max(log_probs, key=log_probs.get))
      return np.array(preds)



class PCA:
    def __init__(self, n_components):
        self.n_components = n_components
        self.components = None
        self.mean = None


    def fit(self, X):
        # Step 1: centre the data
        self.mean = X.mean(axis=0)
        X_centered = X - self.mean


        # Step 2: covariance matrix
        cov = np.cov(X_centered.T)  # shape: (n_features, n_features)


        # Step 3: eigendecomposition
        eigenvalues, eigenvectors = np.linalg.eig(cov)


        # Step 4: sort by eigenvalue descending
        order = np.argsort(eigenvalues)[::-1]
        eigenvalues  = eigenvalues[order]
        eigenvectors = eigenvectors[:, order]


        # Step 5: keep top n_components
        self.components = eigenvectors[:, :self.n_components]


        # Store explained variance ratio
        total_var = eigenvalues.sum()
        self.explained_variance_ratio = eigenvalues[:self.n_components] / total_var


    def transform(self, X):
        return (X - self.mean) @ self.components
