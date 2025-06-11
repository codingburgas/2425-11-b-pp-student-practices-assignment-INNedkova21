import numpy as np
import pickle
from keras.src.datasets import mnist

np.random.seed(42)

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train = x_train.reshape(-1, 28*28) / 255.0
x_test = x_test.reshape(-1, 28*28) / 255.0

def one_hot(y, num_classes=10):
    return np.eye(num_classes)[y]

y_train_oh = one_hot(y_train)
y_test_oh = one_hot(y_test)

# Leaky ReLU
def leaky_relu(x, alpha=0.01): return np.where(x > 0, x, alpha * x)
def leaky_relu_deriv(x, alpha=0.01): return np.where(x > 0, 1, alpha)

def softmax(x):
    e_x = np.exp(x - np.max(x, axis=1, keepdims=True))
    return e_x / np.sum(e_x, axis=1, keepdims=True)

def cross_entropy(pred, y_true):
    m = y_true.shape[0]
    return -np.sum(y_true * np.log(pred + 1e-9)) / m

def accuracy(pred, y_true):
    return np.mean(np.argmax(pred, axis=1) == np.argmax(y_true, axis=1))

# Инициализация на тегла
def init_weights(sizes):
    params = []
    for i in range(len(sizes) - 1):
        W = np.random.randn(sizes[i], sizes[i+1]) * 0.01
        b = np.zeros((1, sizes[i+1]))
        params.append((W, b))
    return params

# Архитектура: 784 → 128 → 64 → 10
sizes = [784, 128, 64, 10]
params = init_weights(sizes)
(W1, b1), (W2, b2), (W3, b3) = params

epochs = 20
lr = 0.05
batch_size = 64

for epoch in range(epochs):
    permutation = np.random.permutation(x_train.shape[0])
    x_train_shuffled = x_train[permutation]
    y_train_shuffled = y_train_oh[permutation]

    for i in range(0, x_train.shape[0], batch_size):
        x_batch = x_train_shuffled[i:i+batch_size]
        y_batch = y_train_shuffled[i:i+batch_size]

        # Forward
        z1 = x_batch @ W1 + b1
        a1 = leaky_relu(z1)
        z2 = a1 @ W2 + b2
        a2 = leaky_relu(z2)
        z3 = a2 @ W3 + b3
        a3 = softmax(z3)

        # Backward
        dz3 = (a3 - y_batch) / batch_size
        dW3 = a2.T @ dz3
        db3 = np.sum(dz3, axis=0, keepdims=True)

        dz2 = dz3 @ W3.T * leaky_relu_deriv(z2)
        dW2 = a1.T @ dz2
        db2 = np.sum(dz2, axis=0, keepdims=True)

        dz1 = dz2 @ W2.T * leaky_relu_deriv(z1)
        dW1 = x_batch.T @ dz1
        db1 = np.sum(dz1, axis=0, keepdims=True)

        # Актуализация
        W3 -= lr * dW3
        b3 -= lr * db3
        W2 -= lr * dW2
        b2 -= lr * db2
        W1 -= lr * dW1
        b1 -= lr * db1

    # Оценка
    z1 = x_test @ W1 + b1
    a1 = leaky_relu(z1)
    z2 = a1 @ W2 + b2
    a2 = leaky_relu(z2)
    z3 = a2 @ W3 + b3
    a3 = softmax(z3)

    loss = cross_entropy(a3, y_test_oh)
    acc = accuracy(a3, y_test_oh)
    print(f"Epoch {epoch+1}/{epochs} - Loss: {loss:.4f} - Accuracy: {acc:.4f}")

# Записване
with open("model/mnist_model.pkl", "wb") as f:
    pickle.dump((W1, b1, W2, b2, W3, b3), f)