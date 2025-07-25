from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
import re
from transformers import pipeline
from PyPDF2 import PdfReader
from dotenv import load_dotenv
load_dotenv()

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
            raw = " ".join([page.extract_text() or "" for page in reader.pages])
            return re.sub(r'\s+', ' ', raw).strip()
    elif path.endswith(".txt"):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""



generator = pipeline(
    "text-generation",
    model="tiiuae/falcon-rw-1b",
    device=-1  # use CPU
)


def generate_feedback(resume_text):
    prompt = (
    "You're a professional recruiter. Give 3 short, helpful, and honest bullet points of resume feedback based on this text:\n\n"
    f"{resume_text[:1000]}\n\n"  # truncate long resumes
    "Feedback:"
    )


    try:
        outputs = generator(prompt, max_new_tokens=100, temperature=0.7)
        
        if not outputs:
            return ["No output from model. Try using a more detailed resume."]

        output = outputs[0]
        if "generated_text" not in output:
            return ["Model did not return any generated text."]

        result = output['generated_text']
        feedback_only = result.split("Feedback:")[-1].strip()

        # Handle empty feedback
        if not feedback_only:
            return ["Model produced empty feedback."]

        # Format bullet points
        lines = feedback_only.split('\n')
        cleaned = [line.strip("•- ") for line in lines if line.strip()]
        return [f"• {line}" for line in cleaned if len(line) > 5]

    except Exception as e:
        return [f"Error generating feedback: {str(e)}"]


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
