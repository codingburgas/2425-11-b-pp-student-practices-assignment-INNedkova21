import os
import numpy as np
from flask import render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
from . import ai
import pickle

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(project_root, 'ai', 'model', 'mnist_model.pkl')

with open(model_path, 'rb') as f:
    W1, b1, W2, b2, W3, b3 = pickle.load(f)

def leaky_relu(x, alpha=0.01): return np.where(x > 0, x, alpha * x)

def predict_digit(image_array_flat):
    z1 = image_array_flat @ W1 + b1
    a1 = leaky_relu(z1)
    z2 = a1 @ W2 + b2
    a2 = leaky_relu(z2)
    z3 = a2 @ W3 + b3
    e_x = np.exp(z3 - np.max(z3))
    softmax = e_x / e_x.sum()
    return int(np.argmax(softmax)), float(np.max(softmax))

@ai.route('/upload', methods=['GET', 'POST'])
def upload():
    prediction = None
    confidence = None

    if request.method == 'POST':
        file = request.files['image']
        if file and file.filename.endswith('.png'):
            filename = secure_filename(file.filename)
            filepath = os.path.join('uploads', filename)
            file.save(filepath)

            image = Image.open(filepath).convert('L')  # Grayscale

            image_array = np.array(image)
            non_empty_columns = np.where(image_array.min(axis=0) < 255)[0]
            non_empty_rows = np.where(image_array.min(axis=1) < 255)[0]
            if non_empty_rows.any() and non_empty_columns.any():
                cropBox = (min(non_empty_columns), min(non_empty_rows),
                           max(non_empty_columns), max(non_empty_rows))
                image = image.crop(cropBox)

            image = image.resize((20, 20), Image.Resampling.LANCZOS)
            new_image = Image.new('L', (28, 28), 255)
            new_image.paste(image, ((28 - 20) // 2, (28 - 20) // 2))

            image_array = np.array(new_image).astype('float32')
            image_array = 255 - image_array  # инверсия
            image_array /= 255.0
            image_array = image_array.reshape(1, 784)

            prediction, conf = predict_digit(image_array)
            confidence = round(conf * 100, 2)

            new_image.save(filepath)

    return render_template('upload.html', prediction=prediction, confidence=confidence)

@ai.route('/draw', methods=['GET', 'POST'])
def draw():
    if request.method == 'POST':
        digit = request.form.get('digit')
        if digit and digit.isdigit() and 0 <= int(digit) <= 9:
            flash(f"Цифрата {digit} е приета!", "success")
            return redirect(url_for('main.draw'))
        else:
            flash("Моля, въведете валидна цифра (0-9).", "danger")
    return render_template("draw.html")