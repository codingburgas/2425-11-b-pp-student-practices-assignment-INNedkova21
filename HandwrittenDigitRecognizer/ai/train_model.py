import numpy as np
import pickle
from keras.src.datasets import mnist

# Set a random seed so we get the same results every time
np.random.seed(42)

# Load training and test data from MNIST (handwritten digits)
(x_train, y_train), (x_test, y_test) = mnist.load_data()

# Make the images flat (28x28 -> 784) and normalize pixel values (0–255 -> 0–1)
x_train = x_train.reshape(-1, 28 * 28) / 255.0
x_test = x_test.reshape(-1, 28 * 28) / 255.0


def one_hot(y, num_classes=10):
    """
    Convert labels (like 3 or 7) into one-hot vectors.
    For example, 3 becomes [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]

    Args:
        y: Array of labels.
        num_classes: Total number of classes (default is 10 for digits 0–9).

    Returns:
        One-hot encoded numpy array.
    """
    return np.eye(num_classes)[y]


# Apply one-hot to training and test labels
y_train_oh = one_hot(y_train)
y_test_oh = one_hot(y_test)


def leaky_relu(x, alpha=0.01):
    """
    Leaky ReLU activation function.
    It allows small values when input is negative, to avoid dead neurons.

    Args:
        x: Input numpy array.
        alpha: Slope for negative values (default 0.01).

    Returns:
        Activated output.
    """
    return np.where(x > 0, x, alpha * x)


def leaky_relu_deriv(x, alpha=0.01):
    """
    Derivative of Leaky ReLU used during backpropagation.

    Args:
        x: Input numpy array.
        alpha: Slope for negative values.

    Returns:
        Derivative of the activation.
    """
    return np.where(x > 0, 1, alpha)


def softmax(x):
    """
    Softmax function converts raw scores into probabilities that sum to 1.

    Args:
        x: 2D array of raw scores.

    Returns:
        Probabilities as a 2D numpy array.
    """
    e_x = np.exp(x - np.max(x, axis=1, keepdims=True))  # For numerical stability
    return e_x / np.sum(e_x, axis=1, keepdims=True)


def cross_entropy(pred, y_true):
    """
    Cross-entropy loss measures how well predictions match the true labels.

    Args:
        pred: Predicted probabilities.
        y_true: True one-hot encoded labels.

    Returns:
        Average loss value.
    """
    m = y_true.shape[0]
    return -np.sum(y_true * np.log(pred + 1e-9)) / m  # Add small value to avoid log(0)


def accuracy(pred, y_true):
    """
    Calculates the percentage of correct predictions.

    Args:
        pred: Predicted probabilities.
        y_true: True one-hot encoded labels.

    Returns:
        Accuracy as a float between 0 and 1.
    """
    return np.mean(np.argmax(pred, axis=1) == np.argmax(y_true, axis=1))


def init_weights(sizes):
    """
    Initializes weights and biases for each layer in the network.

    Args:
        sizes: List of layer sizes, e.g., [784, 128, 64, 10]

    Returns:
        List of tuples (W, b) for each layer.
    """
    params = []
    for i in range(len(sizes) - 1):
        W = np.random.randn(sizes[i], sizes[i + 1]) * 0.01
        b = np.zeros((1, sizes[i + 1]))
        params.append((W, b))
    return params


# Define the size of each layer in the network
sizes = [784, 128, 64, 10]
params = init_weights(sizes)
(W1, b1), (W2, b2), (W3, b3) = params

# Set training parameters
epochs = 20  # number of full passes through the data
lr = 0.05  # learning rate
batch_size = 64  # how many samples to train at once

# Training the neural network
for epoch in range(epochs):
    # Shuffle the training data
    permutation = np.random.permutation(x_train.shape[0])
    x_train_shuffled = x_train[permutation]
    y_train_shuffled = y_train_oh[permutation]

    # Train in small batches
    for i in range(0, x_train.shape[0], batch_size):
        x_batch = x_train_shuffled[i:i + batch_size]
        y_batch = y_train_shuffled[i:i + batch_size]

        # ---- Forward pass (make predictions) ----
        z1 = x_batch @ W1 + b1
        a1 = leaky_relu(z1)
        z2 = a1 @ W2 + b2
        a2 = leaky_relu(z2)
        z3 = a2 @ W3 + b3
        a3 = softmax(z3)  # final output

        # ---- Backward pass (learn from mistakes) ----
        dz3 = (a3 - y_batch) / batch_size
        dW3 = a2.T @ dz3
        db3 = np.sum(dz3, axis=0, keepdims=True)

        dz2 = dz3 @ W3.T * leaky_relu_deriv(z2)
        dW2 = a1.T @ dz2
        db2 = np.sum(dz2, axis=0, keepdims=True)

        dz1 = dz2 @ W2.T * leaky_relu_deriv(z1)
        dW1 = x_batch.T @ dz1
        db1 = np.sum(dz1, axis=0, keepdims=True)

        # ---- Update weights (learn) ----
        W3 -= lr * dW3
        b3 -= lr * db3
        W2 -= lr * dW2
        b2 -= lr * db2
        W1 -= lr * dW1
        b1 -= lr * db1

    # ---- Test the model on test data ----
    z1 = x_test @ W1 + b1
    a1 = leaky_relu(z1)
    z2 = a1 @ W2 + b2
    a2 = leaky_relu(z2)
    z3 = a2 @ W3 + b3
    a3 = softmax(z3)

    # Calculate test loss and accuracy
    loss = cross_entropy(a3, y_test_oh)
    acc = accuracy(a3, y_test_oh)
    print(f"Epoch {epoch+1}/{epochs} - Loss: {loss:.4f} - Accuracy: {acc:.4f}")

# Save the learned weights and biases to a file
with open("model/mnist_model.pkl", "wb") as f:
    pickle.dump((W1, b1, W2, b2, W3, b3), f)