from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import re

from PyPDF2 import PdfReader

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'txt'}

os.makedirs('uploads', exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(path):
    if path.endswith(".pdf"):
        with open(path, 'rb') as f:
            reader = PdfReader(f)
            return " ".join([page.extract_text() or "" for page in reader.pages])
    elif path.endswith(".txt"):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

def generate_feedback(text):
    feedback = []
    if len(text.split()) < 150:
        feedback.append("Your resume seems too short. Aim for at least 1 page of content.")

    if not re.search(r'\b(email|phone|linkedin|contact)\b', text, re.IGNORECASE):
        feedback.append("Missing clear contact information (email, phone, etc).")

    if not re.findall(r'•|-|\*', text):
        feedback.append("Use bullet points to make content easier to scan.")

    if "skills" not in text.lower():
        feedback.append("Include a 'Skills' section to highlight your technical abilities.")

    if not re.findall(r'\b(designed|developed|led|managed|built|created|implemented)\b', text, re.IGNORECASE):
        feedback.append("Use strong action verbs to begin bullet points.")

    if not feedback:
        feedback.append("Your resume looks structurally sound. Great job!")

    return feedback

@app.route("/", methods=["GET", "POST"])
def index():
    feedback = None
    if request.method == "POST":
        file = request.files["resume"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            text = extract_text(filepath)
            feedback = generate_feedback(text)

    return render_template("index.html", feedback=feedback)

if __name__ == "__main__":
    app.run(debug=False)
