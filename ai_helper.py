def get_ai_feedback(prediction, skills, score):

    feedback = []

    if score < 60:
        feedback.append("Improve your resume formatting and add stronger projects.")

    if "python" not in skills:
        feedback.append("Add Python projects to improve technical strength.")

    if "sql" not in skills:
        feedback.append("Learn SQL and database concepts.")

    if "github" not in skills:
        feedback.append("Upload your projects on GitHub.")

    if "communication" not in skills:
        feedback.append("Mention teamwork and communication experience.")

    if prediction.lower() == "data science":
        feedback.append("Add Machine Learning and Data Analysis projects.")

    if prediction.lower() == "web developer":
        feedback.append("Add React and Flask full-stack projects.")

    return feedback