import os
import numpy as np
from flask import render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
from scipy.ndimage import center_of_mass, shift, binary_dilation
from . import ai
import datetime
from flask import send_from_directory, abort
from flask_login import current_user, login_required
import pickle

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_path = os.path.join(project_root, 'ai', 'model', 'mnist_model.pkl')

upload_folder = os.path.join(project_root, 'uploads')
os.makedirs(upload_folder, exist_ok=True)

with open(model_path, 'rb') as f:
    W1, b1, W2, b2, W3, b3 = pickle.load(f)

def leaky_relu(x, alpha=0.01):
    return np.where(x > 0, x, alpha * x)

def predict_digit(image_array_flat):
    z1 = image_array_flat @ W1 + b1
    a1 = leaky_relu(z1)
    z2 = a1 @ W2 + b2
    a2 = leaky_relu(z2)
    z3 = a2 @ W3 + b3
    e_x = np.exp(z3 - np.max(z3, axis=1, keepdims=True))
    softmax = e_x / np.sum(e_x, axis=1, keepdims=True)
    return int(np.argmax(softmax)), float(np.max(softmax))

@ai.route('/upload', methods=['GET', 'POST'])
def upload():
    prediction = None
    confidence = None
    error = None

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename.lower().endswith('.png'):
            filename = secure_filename(file.filename)

            # upload_folder = os.path.join(project_root, 'uploads')
            # os.makedirs(upload_folder, exist_ok=True)

            user_folder = os.path.join(upload_folder, str(current_user.ID))
            os.makedirs(user_folder, exist_ok=True)

            save_path = os.path.join(user_folder, filename)
            file.save(save_path)

            image = Image.open(save_path).convert('L')
            image_array = 255 - np.array(image)

            image_array = (image_array > 50).astype(np.uint8)

            image_array = binary_dilation(image_array, iterations=1).astype(np.uint8) * 255

            coords = np.argwhere(image_array)
            if coords.size == 0:
                error = "No digit found in the image."
                return render_template('upload.html', prediction=None, confidence=None, error=error)

            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0)

            margin = 20
            y0 = max(0, y0 - margin)
            x0 = max(0, x0 - margin)
            y1 = min(image_array.shape[0], y1 + margin)
            x1 = min(image_array.shape[1], x1 + margin)

            cropped = image_array[y0:y1, x0:x1]

            pil_cropped = Image.fromarray(cropped)
            pil_resized = pil_cropped.resize((20, 20), Image.Resampling.LANCZOS)
            resized_arr = np.array(pil_resized)

            canvas = np.zeros((28, 28), dtype=np.uint8)
            canvas[4:24, 4:24] = resized_arr

            cy, cx = center_of_mass(canvas)
            rows, cols = canvas.shape
            shiftx = np.round(cols / 2 - cx).astype(int)
            shifty = np.round(rows / 2 - cy).astype(int)

            final_img = shift(canvas, shift=[shifty, shiftx])

            final_img = final_img / 255.0
            final_img = final_img.reshape(1, 784)

            prediction, conf = predict_digit(final_img)
            confidence = round(conf * 100, 2)

            debug_img = Image.fromarray((255 - final_img.reshape(28,28)*255).astype(np.uint8))
            debug_img.save(save_path)

        else:
            error = "Please upload a valid PNG image."

    return render_template('upload.html', prediction=prediction, confidence=confidence, error=error)

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


@ai.route('/history')
@login_required
def history():
    user_folder = os.path.join(upload_folder, str(current_user.ID))
    images = []

    if os.path.exists(user_folder):
        for filename in os.listdir(user_folder):
            filepath = os.path.join(user_folder, filename)
            if os.path.isfile(filepath):
                upload_time_str = datetime.datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M')
                upload_time_dt = datetime.datetime.strptime(upload_time_str, '%Y-%m-%d %H:%M')
                images.append({'filename': filename, 'upload_time': upload_time_str, 'upload_time_dt': upload_time_dt})

        # Сортиране по дата, най-новите снимки първи
        images.sort(key=lambda x: x['upload_time_dt'], reverse=True)

    return render_template('history.html', images=images)


@ai.route('/download/<filename>')
@login_required
def download_image(filename):
    user_folder = os.path.join(upload_folder, str(current_user.ID))
    filepath = os.path.join(user_folder, filename)
    if os.path.exists(filepath):
        return send_from_directory(user_folder, filename, as_attachment=True)
    else:
        abort(404)


@ai.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_image(filename):
    user_folder = os.path.join(upload_folder, str(current_user.ID))
    filepath = os.path.join(user_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('ai.history'))