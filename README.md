1. Core Purpose
The purpose of this project is to analyze blood sample images (microscopic slides) through a user-friendly web interface and instantly determine whether a patient has leukemia, and if so, what type it is.

2. Technical Workflow
Deep Learning Model: You have trained a fine-tuned model based on the DenseNet architecture that extracts details (features) from images.

Accuracy Boost (TTA): To improve the reliability of predictions, you are using Test-Time Augmentation (TTA), which views the same image from different angles to make better decisions.

Explainable AI (Grad-CAM/SHAP): This not only provides results but also shows via a heatmap which part of the image the model used to detect leukemia, which is very helpful for doctors.

3. Key Features
Leukemia Detection: As soon as an image is uploaded, the system indicates whether the patient is "healthy" or has a specific leukemia type.

Medical Chatbot: This uses the Groq API (Llama 3.1/3.3 models) to provide information about various diseases to the user and answer their questions in natural language.

Web Dashboard: A modern frontend where users can easily drag and drop files and view results in a graphical format.

4. Technology Stack
Backend: Flask (Python).

Frontend: HTML5, CSS3, and JavaScript.

AI/ML: TensorFlow/Keras and Groq Cloud API.

## 5. Running Locally

To run this project on your local machine:

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables:**
    Create a `.env` file in the root directory and add your Groq API key:
    ```env
    GROQ_API_KEY=your_api_key_here
    ```

3.  **Start the Server:**
    Run the `run_local.py` script from the root directory:
    ```bash
    python run_local.py
    ```
    The application will be available at `http://127.0.0.1:5000`.

## 6. Deployment

This project is configured for deployment on Vercel. The `api/index.py` handles the serverless function logic, and `vercel.json` defines the routes and runtimes.
