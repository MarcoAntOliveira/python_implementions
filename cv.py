from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
import numpy as np
from ml import NeuralNetwork




d = load_digits()
X = d.data / 16.0                      # (m, 64)
Y = np.eye(10)[d.target]               # one-hot (m, 10)
Xtr, Xte, Ytr, Yte = train_test_split(X, Y, test_size=0.2, random_state=0)

net = NeuralNetwork([64, 32, 10])
net.train(Xtr.T, Ytr.T, epochs=3000, lr=0.5)

pred, _ = net.predict(Xte.T)
print("acurácia:", np.mean(pred == Yte.argmax(1)))
net.save("nn.npz")

def preprocess(img_gray, size=8):
    """Imagem em tons de cinza -> vetor (size*size, 1), valores 0..1."""
    import cv2
    small = cv2.resize(img_gray, (size, size), interpolation=cv2.INTER_AREA)
    return (small.astype(np.float32) / 255.0).reshape(-1, 1)
import cv2
from ml import NeuralNetwork

net = NeuralNetwork.load("nn.npz")
cap = cv2.VideoCapture(0)

while True:
    ok, frame = cap.read()
    if not ok: break
    img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    h, w = img.shape
    s = min(h, w) // 2
    y0, x0 = h // 2 - s // 2, w // 2 - s // 2
    roi = img[y0:y0 + s, x0:x0 + s]            # <- aqui nasce o roi

    x = preprocess(roi)                        # troque por 1 - x se o dígito for escuro em fundo claro
    cls, conf = net.predict(x)

    cv2.rectangle(frame, (x0, y0), (x0 + s, y0 + s), (0, 255, 0), 2)
    cv2.putText(frame, f"{int(cls[0])} ({float(conf[0]):.2f})", (x0, y0 - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.imshow("teste", frame)
    if cv2.waitKey(1) == 27: break             # ESC sai

cap.release()
cv2.destroyAllWindows()