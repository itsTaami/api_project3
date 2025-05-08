# === user.py ===
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import difflib
import pandas as pd
import joblib
from typing import List
from fastapi import Query, Body
from supabase import create_client, Client

router = APIRouter()

SUPABASE_URL = "https://gqajdjmciuzhiwcqniho.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxYWpkam1jaXV6aGl3Y3FuaWhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE4Mzk2MDQsImV4cCI6MjA1NzQxNTYwNH0.m719elC1ldMX51cBJuv4fhlbPq3jyf5Z_z4relZvVQo"

# Connect to Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Fetch data
response = supabase.table("movies").select("*").execute()
if not response.data:
    raise HTTPException(status_code=500, detail="Failed to fetch movies")
df = pd.DataFrame(response.data)

vectorizer = joblib.load("model.joblib")
similarity = joblib.load("similarity_matrix.joblib")

class RecommendRequest(BaseModel):
    movie_name: str

class PlaylistRequest(BaseModel):
    id: int
    username: str
    playlist_name: str
    movie_title: str = ""


class AddPlaylist(BaseModel):
    
    movie_title: str = ""
    playlist_id: int


class UserRequest(BaseModel):
    id: int
    username: str
    email: str = ""
    password: str

@router.post("/create_user")
def create_user(req: UserRequest):
    # Check if user exists
    existing = supabase.table("users").select("id").eq("id", req.id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="User ID already exists")

    # Insert new user
    supabase.table("users").insert({
        "id": req.id,
        "username": req.username,
        "email": req.email,
        "password": req.password
    }).execute()
    return {"message": "User created"}


@router.post("/recommend")
def recommend_movies(req: RecommendRequest):
    # Step 1: Fetch movie data from Supabase
    response = supabase.table("movies").select("*").execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to fetch movies")
    
    df = pd.DataFrame(response.data)
    
    # Step 2: Vectorize movie titles
    if "title" not in df.columns:
        raise HTTPException(status_code=500, detail="Missing 'title' column in data")

    titles = df['title'].fillna("").tolist()
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(titles)
    
    # Step 3: Find the closest match
    movie_name = req.movie_name
    matches = difflib.get_close_matches(movie_name, titles)
    if not matches:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    close_match = matches[0]
    index = df[df['title'] == close_match].index[0]
    
    # Step 4: Compute similarity
    similarity = cosine_similarity(tfidf_matrix[index], tfidf_matrix).flatten()
    scores = list(enumerate(similarity))
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)[1:21]  # exclude the movie itself
    
    # Step 5: Build recommendations list safely
    recommended = [df.iloc[i[0]]["title"] for i in sorted_scores if i[0] < len(df)]
    
    return {
        "input": movie_name,
        "matched_title": close_match,
        "recommendations": recommended
    }
    
@router.get("/user_playlists")
def get_user_playlists(username: str, id: int):
    response = supabase.table("playlists").select("id, name").eq("username", username).execute()
    return response.data

@router.get("/playlist/{playlist_id}")
def get_playlist_movies(playlist_id: int):
    response = supabase.table("playlists").select("name, movies").eq("id", playlist_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return response.data

@router.post("/create_playlist")
def create_playlist(req: PlaylistRequest):
    # Check for duplicate ID
    existing = supabase.table("playlists").select("id").eq("id", req.id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Playlist ID already exists")

    # Insert new playlist
    result = supabase.table("playlists").insert({
        "id": req.id,
        "username": req.username,
        "name": req.playlist_name,
        "movies": []
    }).execute()

    return {"message": "Playlist created", "playlist_id": req.id}

@router.post("/add_to_playlist")
def add_to_playlist(req: AddPlaylist):
    # Fetch existing playlist
    response = supabase.table("playlists").select("movies").eq("id", req.playlist_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Playlist not found")

    current_movies = response.data["movies"] or []
    current_movies.append(req.movie_title)

    # Update playlist
    supabase.table("playlists").update({"movies": current_movies}).eq("id", req.playlist_id).execute()
    return {"message": f"Movie '{req.movie_title}' added to playlist {req.playlist_id}"}

@router.delete("/remove_from_playlist")
def remove_from_playlist(playlist_id: int = Query(...), movie_title: str = Query(...)):
    # Fetch existing playlist
    response = supabase.table("playlists").select("movies").eq("id", playlist_id).single().execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Playlist not found")

    current_movies = response.data["movies"] or []

    # Remove the movie if it exists
    if movie_title not in current_movies:
        raise HTTPException(status_code=404, detail="Movie not found in playlist")

    current_movies.remove(movie_title)

    # Update the playlist
    supabase.table("playlists").update({"movies": current_movies}).eq("id", playlist_id).execute()
    return {"message": f"Movie '{movie_title}' removed from playlist {playlist_id}"}

@router.delete("/delete_playlist/{playlist_id}")
def delete_playlist(playlist_id: int):
    response = supabase.table("playlists").delete().eq("id", playlist_id).execute()
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Playlist not found or already deleted")
    return {"message": "Playlist deleted"}