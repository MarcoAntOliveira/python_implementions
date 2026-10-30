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

class KMeans:
    def __init__(self, k=3, max_iters=100):
        self.k = k
        self.max_iters = max_iters


    def fit(self, X):
        # Random init: pick K points from data as starting centroids
        idx = np.random.choice(len(X), self.k, replace=False)
        self.centroids = X[idx]


        for _ in range(self.max_iters):
            # Assign step: compute distances to each centroid
            distances = np.array([
                np.linalg.norm(X - c, axis=1) for c in self.centroids
            ])  # shape: (k, n_samples)
            labels = np.argmin(distances, axis=0)


            # Update step: new centroid = mean of cluster members
            new_centroids = np.array([
                X[labels == k].mean(axis=0) for k in range(self.k)
            ])


            # Convergence check
            if np.allclose(self.centroids, new_centroids):
                break
            self.centroids = new_centroids


        self.labels = labels
        return self

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
