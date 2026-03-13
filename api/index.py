import os
import numpy as np
import tensorflow as tf
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from tensorflow.keras.preprocessing.image import ImageDataGenerator, img_to_array, load_img
from groq import Groq
from dotenv import load_dotenv
import time

# --- Initialize Environment Variables ---
load_dotenv()

# --- App Instance Configuration ---
# Determine directories
API_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(API_DIR, '..'))

app = Flask(__name__, 
            template_folder=os.path.join(PROJECT_ROOT, 'templates'),
            static_folder=os.path.join(PROJECT_ROOT, 'static'))
CORS(app)

# --- File Paths ---
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
STATIC_IMAGES = os.path.join(PROJECT_ROOT, 'static', 'images')
# The model is located in the api directory
MODEL_PATH = os.path.join(API_DIR, 'fine_tuned_densenet_leukemia (1).h5')

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Load Model ---
model = None

def get_model():
    global model
    if model is not None:
        return model
    
    if not os.path.exists(MODEL_PATH):
        print(f"CRITICAL ERROR: Model file not found at {MODEL_PATH}")
        return None
        
    try:
        print(f"Instantiating Inference Model from {MODEL_PATH}...")
        model = tf.keras.models.load_model(MODEL_PATH, compile=False)
        return model
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return None

# --- Groq Client (Using Environment Variables) ---
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

try:
    if GROQ_API_KEY:
        groq_client = Groq(api_key=GROQ_API_KEY)
    else:
        print("WARNING: GROQ_API_KEY not found in environment variables.")
        groq_client = None
except Exception as e:
    print(f"Groq Initialization Error: {e}")
    groq_client = None

# --- Classification Configuration ---
CLASS_NAMES = [
    'Acute Lymphoblastic Leukemia (ALL)', 
    'Acute Myeloid Leukemia (AML)', 
    'Chronic Lymphocytic Leukemia (CLL)', 
    'Chronic Myeloid Leukemia (CML)',
    'Healthy / Normal'
]

BALANCING_WEIGHTS = np.array([2.2, 1.8, 1.0, 0.8, 1.0])

def predict_with_tta(image_path, tta_steps=5):
    loaded_model = get_model()
    if not loaded_model:
        raise Exception("Diagnostic Model currently offline.")

    img = load_img(image_path, target_size=(224, 224))
    img_array = img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    datagen = ImageDataGenerator(
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.1
    )

    preds = []
    for i in range(tta_steps):
        it = datagen.flow(img_array, batch_size=1)
        batch = next(it)
        preds.append(loaded_model.predict(batch, verbose=0))

    avg_pred = np.mean(preds, axis=0)[0]
    num_classes = len(avg_pred)
    
    active_weights = np.ones(num_classes)
    if num_classes > 0: active_weights[0] = 2.2 # ALL
    if num_classes > 1: active_weights[1] = 1.8 # AML
    if num_classes > 3: active_weights[3] = 0.8 # CML

    weighted_pred = avg_pred * active_weights
    class_idx = np.argmax(weighted_pred)
    
    label = CLASS_NAMES[class_idx] if class_idx < len(CLASS_NAMES) else f"Cell Type {class_idx}"
    conf = float(avg_pred[class_idx])

    return label, conf

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file segment found'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    tmp_path = os.path.join('/tmp', f"scan_{int(time.time())}.jpg") if os.path.exists('/tmp') else os.path.join(UPLOAD_FOLDER, "current_scan.jpg")
    file.save(tmp_path)

    try:
        label, conf = predict_with_tta(tmp_path)
        heatmap_url = "/static/images/mock_heatmap.png"

        return jsonify({
            'prediction': label,
            'confidence': conf,
            'heatmap_url': heatmap_url,
            'status': 'success'
        })
    except Exception as e:
        print(f"Prediction Failure: {str(e)}")
        return jsonify({'error': f"Processing Error: {str(e)}"}), 500
    finally:
        if os.path.exists(tmp_path) and "/tmp" in tmp_path:
            os.remove(tmp_path)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Invalid request payload'}), 400

    if not groq_client:
        return jsonify({'response': "Assistant offline (Invalid API configuration)."}), 500

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional medical assistant specialized in Leukemia. Provide clear information about ALL, AML, CLL, and CML types. Always remind users that findings require clinical verification by a hematologist."},
                {"role": "user", "content": data['message']}
            ],
            timeout=10
        )
        return jsonify({'response': completion.choices[0].message.content})
    except Exception as e:
        print(f"Groq connectivity error: {str(e)}")
        return jsonify({'response': "Network error occurred while contacting the clinical knowledge base."}), 200

@app.route('/status')
def status():
    return jsonify({
        'deployment': 'Vercel Serverless',
        'backend': 'Flask-CORS',
        'ai_model': 'DenseNet-Leukemia-Inference',
        'device': 'CPU (Forced)',
        'groq_active': groq_client is not None
    })

if __name__ == '__main__':
    get_model()
    app.run(debug=True, port=5000)
