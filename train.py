import pandas as pd
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Load dataset
df = pd.read_csv("dataset/Resume.csv")

print("Columns:", df.columns)

# Clean dataset
df = df.dropna()

# Features and labels
X = df["Resume_str"]
y = df["Category"]

# Convert text to numbers
vectorizer = TfidfVectorizer(stop_words="english", max_features=3000)
X_vec = vectorizer.fit_transform(X)

# Train model (UPGRADED)
model = LogisticRegression(max_iter=1000)
model.fit(X_vec, y)

# Save model folder
os.makedirs("model", exist_ok=True)

# Save model + vectorizer
pickle.dump(model, open("model/model.pkl", "wb"))
pickle.dump(vectorizer, open("model/vectorizer.pkl", "wb"))

print("Model trained successfully 🚀")