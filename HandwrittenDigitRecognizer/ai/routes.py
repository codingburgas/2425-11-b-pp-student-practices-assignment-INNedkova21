import os
from tkinter import Image
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from keras.src.saving import load_model
from werkzeug.utils import secure_filename
from PIL import Image
from . import ai

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(project_root, 'ai', 'mnist_model.h5')

model = load_model(model_path)

@ai.route('/upload', methods=['GET', 'POST'])
def upload():
    prediction = None

    if request.method == 'POST':
        file = request.files['image']
        if file and file.filename.endswith('.png'):
            filename = secure_filename(file.filename)
            filepath = os.path.join('static/uploads', filename)
            file.save(filepath)

            image = Image.open(filepath).convert('L')
            image = image.resize((28, 28))
            image_array = np.array(image)
            image_array = 255 - image_array
            image_array = image_array / 255.0
            image_array = image_array.reshape(1, 28, 28, 1)

            pred = model.predict(image_array)
            prediction = int(np.argmax(pred))

    return render_template('upload.html', prediction=prediction)

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