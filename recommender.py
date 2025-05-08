# === model/recommender.py ===
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CSV_PATH = "movies.csv"

def train_and_save():
    df = pd.read_csv(CSV_PATH)
    selected_features = ['genres','keywords','tagline','cast','director']
    for feature in selected_features:
        df[feature] = df[feature].fillna('')
    combined = df['genres']+' '+df['keywords']+' '+df['tagline']+' '+df['cast']+' '+df['director']
    vectorizer = TfidfVectorizer()
    features = vectorizer.fit_transform(combined)
    similarity = cosine_similarity(features)
    joblib.dump(vectorizer, "model.joblib")
    joblib.dump(similarity, "similarity_matrix.joblib")
    print("Model and similarity matrix saved.")

if __name__ == "__main__":
    train_and_save()