from flask import render_template, request, redirect, url_for, flash, send_from_directory, jsonify, abort
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from ..models.prediction import Prediction
from ..models.user import User
from ..extensions import db
from . import ai
import os
import numpy as np
from PIL import Image
from scipy.ndimage import center_of_mass, shift
from scipy.ndimage import binary_dilation
from datetime import datetime
import base64
from io import BytesIO
import pickle

# Get the root directory of the project
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Path to the trained MNIST model
model_path = os.path.join(project_root, 'ai', 'model', 'mnist_model.pkl')

# Folder where uploaded images will be stored
upload_folder = os.path.join(project_root, 'uploads')
os.makedirs(upload_folder, exist_ok=True)

# Load trained neural network weights and biases
with open(model_path, 'rb') as f:
    W1, b1, W2, b2, W3, b3 = pickle.load(f)

def leaky_relu(x, alpha=0.01):
    """Leaky ReLU activation function."""
    return np.where(x > 0, x, alpha * x)

def predict_digit(image_array_flat):
    """Predict the digit from a flattened image array."""
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
    """Route for uploading an image to predict a digit."""
    prediction = None
    confidence = None
    error = None

    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename.lower().endswith('.png'):
            filename = secure_filename(file.filename)

            # Create a folder for the current user if it doesn't exist
            user_folder = os.path.join(upload_folder, str(current_user.ID))
            os.makedirs(user_folder, exist_ok=True)

            save_path = os.path.join(user_folder, filename)
            file.save(save_path)

            # Preprocess image
            image = Image.open(save_path).convert('L')
            image_array = 255 - np.array(image)
            image_array = (image_array > 50).astype(np.uint8)
            image_array = binary_dilation(image_array, iterations=1).astype(np.uint8) * 255

            # Find digit area
            coords = np.argwhere(image_array)
            if coords.size == 0:
                error = "No digit found in the image."
                return render_template('upload.html', prediction=None, confidence=None, error=error)

            # Crop the image around the digit with margin
            y0, x0 = coords.min(axis=0)
            y1, x1 = coords.max(axis=0)
            margin = 20
            y0 = max(0, y0 - margin)
            x0 = max(0, x0 - margin)
            y1 = min(image_array.shape[0], y1 + margin)
            x1 = min(image_array.shape[1], x1 + margin)

            cropped = image_array[y0:y1, x0:x1]

            # Resize to 20x20 and center on 28x28 canvas
            pil_cropped = Image.fromarray(cropped)
            pil_resized = pil_cropped.resize((20, 20), Image.Resampling.LANCZOS)
            resized_arr = np.array(pil_resized)

            canvas = np.zeros((28, 28), dtype=np.uint8)
            canvas[4:24, 4:24] = resized_arr

            # Center the digit
            cy, cx = center_of_mass(canvas)
            rows, cols = canvas.shape
            shiftx = np.round(cols / 2 - cx).astype(int)
            shifty = np.round(rows / 2 - cy).astype(int)
            final_img = shift(canvas, shift=[shifty, shiftx])

            # Normalize and reshape for prediction
            final_img = final_img / 255.0
            final_img = final_img.reshape(1, 784)

            # Predict digit
            prediction, conf = predict_digit(final_img)
            confidence = round(conf * 100, 2)

            # Save processed image
            debug_img = Image.fromarray((255 - final_img.reshape(28,28)*255).astype(np.uint8))
            debug_img.save(save_path)

            # Save prediction to database
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
    """Route for drawing a digit on a canvas and predicting it."""
    prediction = None
    confidence = None

    if request.method == 'POST':
        image_data = request.form.get('image_data')
        if image_data:
            try:
                # Decode base64 image data
                header, encoded = image_data.split(",", 1)
                binary_data = base64.b64decode(encoded)
                image = Image.open(BytesIO(binary_data))

                # Preprocess image
                processed = preprocess_canvas_image(image)
                if processed is None:
                    return render_template('draw.html')

                user_folder = os.path.join(upload_folder, str(current_user.ID))
                os.makedirs(user_folder, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"drawn_{timestamp}.png"
                save_path = os.path.join(user_folder, filename)

                # Save processed image for debugging
                debug_array = (1.0 - processed.reshape(28, 28)) * 255
                debug_img = Image.fromarray(debug_array.astype(np.uint8))
                debug_img.save(save_path)

                # Predict digit
                prediction, conf = predict_digit(processed)
                confidence = round(conf * 100, 2)

                # Save prediction to database
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
                print("ГРЕШКА:", e)

    return render_template('draw.html', prediction=prediction, confidence=confidence)

def preprocess_canvas_image(image):
    """Preprocess image drawn on the canvas for prediction."""
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
    shifted = shifted / 255.0  # Normalize image
    return shifted.reshape(1, 784)

@ai.route('/history')
@login_required
def history():
    """Route to show prediction history for the current user or all if admin."""
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

        # Форматиране на датата в български формат
        upload_time_str = prediction.CreatedAt.strftime('%d.%m.%Y %H:%M')
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
    """
    Allows a logged-in user to download an image by filename.
    Admins can download images from all users, others can only access their own.
    """
    filename = secure_filename(filename)

    if not os.path.exists(upload_folder):
        abort(404)

    if current_user.Role == 'Administrator':
        # Admin can search through all user folders
        for user_folder_name in os.listdir(upload_folder):
            user_folder = os.path.join(upload_folder, user_folder_name)
            filepath = os.path.join(user_folder, filename)
            if os.path.exists(filepath):
                return send_from_directory(user_folder, filename, as_attachment=True)
    else:
        # Regular user can only download their own images
        user_folder = os.path.join(upload_folder, str(current_user.ID))
        filepath = os.path.join(user_folder, filename)
        if os.path.exists(filepath):
            return send_from_directory(user_folder, filename, as_attachment=True)

    abort(404)  # File not found


@ai.route('/delete/<filename>', methods=['POST'])
@login_required
def delete_image(filename):
    """
    Deletes a specific image file and its associated prediction record.
    Admins can delete any image, regular users only their own.
    """
    filename = secure_filename(filename)
    deleted = False

    # Try to find the prediction entry in the database
    prediction = Prediction.query.filter(Prediction.ImagePath.like(f"%{filename}")).first()

    if not os.path.exists(upload_folder):
        return redirect(url_for('ai.history'))

    if current_user.Role == 'Administrator':
        # Admin checks all user folders
        for user_folder_name in os.listdir(upload_folder):
            folder_path = os.path.join(upload_folder, user_folder_name)
            file_path = os.path.join(folder_path, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted = True
                break
    else:
        # Regular user only deletes from their folder
        user_folder = os.path.join(upload_folder, str(current_user.ID))
        file_path = os.path.join(user_folder, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            deleted = True

    if prediction:
        try:
            db.session.delete(prediction)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash('Грешка при изтриване от базата: ' + str(e), 'danger')

    next_page = request.args.get('next')

    if next_page == 'admin_user_details':
        # Optional redirection to admin user details page
        return redirect(url_for('users.admin_user_details'))
    else:
        return redirect(url_for('ai.history'))


@ai.route('/delete_prediction/<int:prediction_id>', methods=['DELETE'])
@login_required
def delete_prediction(prediction_id):
    """
    Deletes a specific prediction by ID.
    Returns JSON response for AJAX requests.
    Only administrators can perform this action.
    """
    if current_user.Role != 'Administrator':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    prediction = Prediction.query.get_or_404(prediction_id)
    
    try:
        # Delete the image file if it exists
        if os.path.exists(prediction.ImagePath):
            os.remove(prediction.ImagePath)
        
        # Delete the prediction record from database
        db.session.delete(prediction)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Prediction deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500