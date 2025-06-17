import base64
import os
from io import BytesIO
import numpy as np
from flask import render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image
from scipy.ndimage import center_of_mass, shift, binary_dilation
from . import ai
from datetime import datetime
from flask import send_from_directory, abort
from flask_login import current_user, login_required
import pickle

from ..extensions import db
from ..models.prediction import Prediction
from ..models.user import User

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
@login_required
def upload():
    prediction = None
    confidence = None
    error = None

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename.lower().endswith('.png'):
            filename = secure_filename(file.filename)

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

            if prediction is not None:
                new_prediction = Prediction(
                    UserID=current_user.ID,
                    ImagePath=save_path,
                    Prediction=prediction,
                    Confidence=confidence,
                    CreatedAt=datetime.now()
                )
                try:
                    db.session.add(new_prediction)
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    error = "Грешка при запис в базата: " + str(e)

        else:
            error = "Please upload a valid PNG image."

    return render_template('upload.html', prediction=prediction, confidence=confidence, error=error)

@ai.route('/draw', methods=['GET', 'POST'])
@login_required
def draw():
    prediction = None
    confidence = None

    if request.method == 'POST':
        image_data = request.form.get('image_data')
        if image_data:
            try:
                header, encoded = image_data.split(",", 1)
                binary_data = base64.b64decode(encoded)
                image = Image.open(BytesIO(binary_data))

                processed = preprocess_canvas_image(image)
                if processed is None:
                    # flash("Не е открита цифра. Опитай отново.", "danger")
                    return render_template('draw.html')

                user_folder = os.path.join(upload_folder, str(current_user.ID))
                os.makedirs(user_folder, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"drawn_{timestamp}.png"
                save_path = os.path.join(user_folder, filename)

                debug_array = (1.0 - processed.reshape(28, 28)) * 255
                debug_img = Image.fromarray(debug_array.astype(np.uint8))
                debug_img.save(save_path)

                prediction, conf = predict_digit(processed)
                confidence = round(conf * 100, 2)

                if prediction is not None:
                    new_prediction = Prediction(
                        UserID=current_user.ID,
                        ImagePath=save_path,
                        Prediction=prediction,
                        Confidence=confidence,
                        CreatedAt=datetime.now()
                    )
                    try:
                        db.session.add(new_prediction)
                        db.session.commit()
                    except Exception as e:
                        db.session.rollback()
                        flash("Грешка при запис в базата: " + str(e), "danger")

            except Exception as e:
                # flash("Възникна грешка при обработката на изображението.", "danger")
                print("ГРЕШКА:", e)

    return render_template('draw.html', prediction=prediction, confidence=confidence)


def preprocess_canvas_image(image):
    image = image.convert('L')
    image_array = 255 - np.array(image)

    image_array = (image_array > 30).astype(np.uint8)
    image_array = binary_dilation(image_array, iterations=1).astype(np.uint8) * 255

    coords = np.argwhere(image_array)
    if coords.size == 0:
        return None

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

    canvas = np.zeros((28, 28), dtype=np.uint8)
    canvas[4:24, 4:24] = np.array(pil_resized)

    cy, cx = center_of_mass(canvas)
    rows, cols = canvas.shape
    shiftx = np.round(cols / 2 - cx).astype(int)
    shifty = np.round(rows / 2 - cy).astype(int)

    shifted = shift(canvas, shift=[shifty, shiftx])
    shifted = shifted / 255.0  # Нормализиране
    return shifted.reshape(1, 784)

@ai.route('/history')
@login_required
def history():
    images = []

    if current_user.Role == 'Administrator':
        predictions = Prediction.query.order_by(Prediction.CreatedAt.desc()).all()
    else:
        predictions = Prediction.query.filter_by(UserID=current_user.ID).order_by(Prediction.CreatedAt.desc()).all()

    for prediction in predictions:
        user = User.query.filter_by(ID=prediction.UserID).first()
        author_name = f"{user.FirstName} {user.LastName}" if user else "Unknown"
        author_email = user.Email if user else "Unknown"
        user_id = user.ID if user else None

        upload_time_str = prediction.CreatedAt.strftime('%Y-%m-%d %H:%M')
        upload_time_dt = prediction.CreatedAt

        images.append({
            'filename': os.path.basename(prediction.ImagePath),
            'upload_time': upload_time_str,
            'upload_time_dt': upload_time_dt,
            'author_name': author_name,
            'author_email': author_email,
            'user_id': user_id
        })

    images.sort(key=lambda x: x['upload_time_dt'], reverse=True)
    return render_template('history.html', images=images)


@ai.route('/download/<filename>')
@login_required
def download_image(filename):
    filename = secure_filename(filename)

    if current_user.Role == 'Administrator':
        # Търси във всички потребителски папки
        for user_folder_name in os.listdir(upload_folder):
            user_folder = os.path.join(upload_folder, user_folder_name)
            filepath = os.path.join(user_folder, filename)
            if os.path.exists(filepath):
                return send_from_directory(user_folder, filename, as_attachment=True)
        abort(404)  # ако не е намерен
    else:
        # Нормален потребител - търси само в неговата папка
        user_folder = os.path.join(upload_folder, str(current_user.ID))
        filepath = os.path.join(user_folder, filename)
        if os.path.exists(filepath):
            return send_from_directory(user_folder, filename, as_attachment=True)
        abort(404)


@ai.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_image(filename):
    if current_user.Role == 'Administrator':
        for user_folder_name in os.listdir(upload_folder):
            folder_path = os.path.join(upload_folder, user_folder_name)
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                break
    else:
        user_folder = os.path.join(upload_folder, str(current_user.ID))
        file_path = os.path.join(user_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    return redirect(url_for('ai.history'))


@ai.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.Role != 'Administrator':
        abort(403)

    user_to_delete = User.query.get_or_404(user_id)

    if user_to_delete.ID == current_user.ID:
        flash('Не можеш да изтриеш собствения си акаунт!', 'warning')
        return redirect(url_for('ai.history'))

    try:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Потребителят {user_to_delete.Email} беше изтрит успешно.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Възникна грешка при изтриването на потребителя.', 'danger')

    return redirect(url_for('ai.history'))