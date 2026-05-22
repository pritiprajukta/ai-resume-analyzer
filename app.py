from flask import Flask, render_template, request, send_file, redirect, session
import pickle
import PyPDF2
import numpy as np
import re
import os
import sqlite3
import matplotlib

# ✅ FIX: Render-safe matplotlib backend
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.pdfgen import canvas

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from database import save_history
from auth import login_user, register_user

# -------------------------
# OPTIONAL AI MODULE
# -------------------------
try:
    from ai_helper import get_ai_feedback
except:
    def get_ai_feedback(prediction, skills, score):
        feedback = []
        if "github" not in skills:
            feedback.append("Upload projects on GitHub")
        if "communication" not in skills:
            feedback.append("Improve communication skills")
        if score < 70:
            feedback.append("Add more projects")
        return feedback

try:
    from job_data import JOB_RECOMMENDATIONS
except:
    JOB_RECOMMENDATIONS = {}

# -------------------------
# APP INIT
# -------------------------
app = Flask(__name__)
app.secret_key = "secret123"

# Ensure folders exist
os.makedirs("static", exist_ok=True)
os.makedirs("model", exist_ok=True)

# -------------------------
# MODEL LOAD (SAFE PATH)
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "model", "model.pkl")
vectorizer_path = os.path.join(BASE_DIR, "model", "vectorizer.pkl")

with open(model_path, "rb") as f:
    model = pickle.load(f)

with open(vectorizer_path, "rb") as f:
    vectorizer = pickle.load(f)

# -------------------------
# SKILLS
# -------------------------
SKILLS = [
    "python", "java", "c++", "sql",
    "machine learning", "deep learning",
    "flask", "django", "react",
    "html", "css", "javascript",
    "pandas", "numpy",
    "git", "github",
    "communication", "teamwork"
]

IMPORTANT_SKILLS = {
    "python": 10,
    "sql": 8,
    "machine learning": 10,
    "deep learning": 9,
    "flask": 7,
    "django": 7,
    "react": 6,
    "github": 5,
    "communication": 8,
    "teamwork": 6
}

MUST_HAVE_SKILLS = ["python", "sql", "communication"]

# -------------------------
# DB INIT (IMPORTANT FOR RENDER)
# -------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        prediction TEXT,
        confidence REAL,
        skills TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------------
# HELPERS
# -------------------------
def extract_skills(text):
    text = text.lower()
    found = []
    for skill in SKILLS:
        if re.search(r"\b" + re.escape(skill) + r"\b", text):
            found.append(skill)
    return list(set(found))


def calculate_resume_score(skills):
    return min(40 + len(skills) * 8, 100)


def calculate_ats_score(resume_text, job_description, skills):
    if not resume_text or not job_description:
        return 0

    tfidf = TfidfVectorizer(stop_words="english")
    matrix = tfidf.fit_transform([resume_text, job_description])
    similarity = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]

    base_score = similarity * 100

    skill_score = 0
    for s in skills:
        skill_score += IMPORTANT_SKILLS.get(s.lower(), 2)

    skill_score = min(skill_score, 40)

    penalty = 0
    for must in MUST_HAVE_SKILLS:
        if must not in skills:
            penalty += 10

    final_score = base_score + skill_score - penalty

    return round(max(0, min(final_score, 100)), 2)


def generate_suggestions(skills):
    suggestions = []
    if "python" not in skills:
        suggestions.append("Learn Python")
    if "sql" not in skills:
        suggestions.append("Learn SQL")
    if "machine learning" not in skills:
        suggestions.append("Build ML projects")
    if "github" not in skills:
        suggestions.append("Upload projects on GitHub")
    return suggestions


def create_pie_chart(classes, probabilities):
    plt.figure(figsize=(7, 7))
    plt.pie(probabilities, labels=classes, autopct='%1.1f%%')
    plt.title("Prediction Distribution")

    path = "static/pie_chart.png"
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    return path


# -------------------------
# GLOBAL
# -------------------------
last_prediction = {}
last_skills = []

# -------------------------
# ROUTES
# -------------------------
@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html", username=session["user"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if login_user(request.form["username"], request.form["password"]):
            session["user"] = request.form["username"]
            return redirect("/")
        return render_template("login.html", error="Invalid login")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            register_user(request.form["username"], request.form["password"])
            return redirect("/login")
        except:
            return render_template("register.html", error="User exists")
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")


# -------------------------
# PREDICT
# -------------------------
@app.route("/predict", methods=["POST"])
def predict():
    global last_prediction, last_skills

    if "user" not in session:
        return redirect("/login")

    file = request.files.get("resume_pdf")
    job_description = request.form.get("job_description", "")

    if not file:
        return "No file uploaded"

    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            if page.extract_text():
                text += page.extract_text()
    except:
        return "PDF error"

    vec = vectorizer.transform([text])
    prediction = model.predict(vec)[0]
    probabilities = model.predict_proba(vec)[0]

    confidence = round(max(probabilities) * 100, 2)

    classes = model.classes_
    top_indices = np.argsort(probabilities)[::-1][:3]

    top_3 = [(classes[i], round(probabilities[i] * 100, 2)) for i in top_indices]

    skills = extract_skills(text)

    resume_score = calculate_resume_score(skills)
    ats_score = calculate_ats_score(text, job_description, skills)

    missing_skills = [s for s in ["python", "sql", "machine learning", "github", "communication"] if s not in skills]

    suggestions = generate_suggestions(skills)

    try:
        ai_feedback = get_ai_feedback(prediction, skills, resume_score)
    except:
        ai_feedback = ["AI unavailable"]

    recommended_jobs = JOB_RECOMMENDATIONS.get(prediction, [])

    chart = create_pie_chart(classes, probabilities)

    username = session.get("user")

    try:
        save_history(username, prediction, confidence, skills)
    except:
        pass

    last_prediction = {
        "prediction": prediction,
        "confidence": confidence,
        "score": resume_score
    }

    last_skills = skills

    return render_template(
        "index.html",
        username=username,
        prediction=prediction,
        confidence=confidence,
        top_3=top_3,
        skills=skills,
        chart=chart,
        score=resume_score,
        ats_score=ats_score,
        suggestions=suggestions,
        missing_skills=missing_skills,
        ai_feedback=ai_feedback,
        recommended_jobs=recommended_jobs
    )


# -------------------------
# DOWNLOAD
# -------------------------
@app.route("/download")
def download():
    if "user" not in session:
        return redirect("/login")

    file = "report.pdf"
    c = canvas.Canvas(file)

    c.drawString(100, 800, "AI Resume Report")
    c.drawString(100, 760, f"Prediction: {last_prediction.get('prediction','')}")
    c.drawString(100, 730, f"Confidence: {last_prediction.get('confidence','')}")
    c.drawString(100, 700, f"Score: {last_prediction.get('score','')}")
    c.drawString(100, 670, f"Skills: {', '.join(last_skills)}")

    c.save()
    return send_file(file, as_attachment=True)


# -------------------------
# HISTORY
# -------------------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM history ORDER BY id DESC")
    data = c.fetchall()
    conn.close()

    return render_template("history.html", data=data)


# -------------------------
# ADMIN
# -------------------------
@app.route("/admin")
def admin():
    if "user" not in session:
        return redirect("/login")

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM history")
    total_predictions = c.fetchone()[0]

    c.execute("SELECT prediction, COUNT(*) FROM history GROUP BY prediction")
    stats = c.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_predictions=total_predictions,
        stats=stats
    )


# -------------------------
# RUN (RENDER SAFE)
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)