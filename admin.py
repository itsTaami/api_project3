# === admin.py ===
from fastapi import APIRouter, HTTPException, Depends
import pandas as pd
import os
import json
from fastapi.responses import JSONResponse
import numpy as np
from supabase import create_client
from typing import Dict
from pydantic import BaseModel
from typing import Optional



router = APIRouter()


SUPABASE_URL = "https://gqajdjmciuzhiwcqniho.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdxYWpkam1jaXV6aGl3Y3FuaWhvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE4Mzk2MDQsImV4cCI6MjA1NzQxNTYwNH0.m719elC1ldMX51cBJuv4fhlbPq3jyf5Z_z4relZvVQo"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


class Movie(BaseModel):
    title: str
    genres: Optional[str] = None
    keywords: Optional[str] = None
    tagline: Optional[str] = None
    cast: Optional[str] = None
    director: Optional[str] = None

class User(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


@router.get("/movies")
def get_movies():
    try:
        # Fetch all movies from the database
        response = supabase.table("movies").select("*").execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No movies found")
        return {"movies": response.data}  # Return the list of movies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 




@router.get("/movies/{movie_id}")
def get_movie(title: str, movie_id: Optional[int] = None):
    try:
        # Fetch movie by Title (required) and optionally by ID
        query = supabase.table("movies").select("*")
        
        query = query.eq("title", title)  # Filter by Title (required)

        if movie_id:
            query = query.eq("id", movie_id)  # Filter by ID if provided

        response = query.execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Movie not found")

        return response.data[0]  # Return the first result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/movies")  # Use POST for inserting movies
def add_movie(movie: Movie):  # Accepting movie input as request body
    try:
        response = supabase.table("movies").insert(movie.dict()).execute()
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to add movie")
        return {"message": "Movie added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/movies/{title}")
def update_movie(title: str, movie: Movie):
    try:
        # Check if the movie exists
        existing = supabase.table("movies").select("title").eq("title", title).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        # Perform the update operation
        response = supabase.table("movies").update(movie.dict()).eq("title", title).execute()

        # Check if the update was successful by inspecting the response data
        if not response.data:  # If no data is returned, the update didn't affect any rows
            raise HTTPException(status_code=400, detail="Failed to update movie")
        
        return {"message": "Movie updated successfully"}

    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
def get_all_users():
    try:
        # Fetch all users
        response = supabase.table("users").select("*").execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="No users found")
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user")
def get_user_by_id_and_username(user_id: Optional[int] = None, username: Optional[str] = None):
    try:
        # Initialize the query
        query = supabase.table("users").select("*")
        
        # Apply filters based on the provided parameters
        if user_id:
            query = query.eq("id", user_id)  # Filter by ID if provided
        if username:
            query = query.eq("username", username)  # Filter by Username if provided
        
        # Execute the query
        response = query.execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
        
        return response.data[0]  # Return the first result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}")
def update_user(user_id: int, user: User):
    try:
        # Check if the user exists
        existing_user = supabase.table("users").select("*").eq("id", user_id).execute()
        if not existing_user.data:
            raise HTTPException(status_code=404, detail="User not found")

        # Perform the update operation
        response = supabase.table("users").update(user.dict()).eq("id", user_id).execute()

        # Check if the update was successful by inspecting the response data
        if not response.data:  # If no data is returned, the update didn't affect any rows
            raise HTTPException(status_code=400, detail="Failed to update user")

        return {"message": "User updated successfully"}

    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(status_code=500, detail=str(e))


# @router.get("/movies")
# def get_movie(movie_id: Optional[int] = None, title: Optional[str] = None):
#     try:
#         # Fetch movie by either ID or Title
#         query = supabase.table("movies").select("*")
        
#         if movie_id:
#             query = query.eq("id", movie_id)  # Filter by ID if provided
#         if title:
#             query = query.eq("title", title)  # Filter by Title if provided

#         response = query.execute()
        
#         if not response.data:
#             raise HTTPException(status_code=404, detail="Movie not found")

#         return response.data[0]  # Return the first result

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))


# Update: Added proper POST handling



@router.delete("/users")
def delete_user(username: Optional[str] = None, user_id: Optional[int] = None):
    try:
        # Initialize the query
        query = supabase.table("users").delete()

        # Apply filter based on the provided parameters
        if username:
            query = query.eq("username", username)
        if user_id:
            query = query.eq("id", user_id)

        # Execute the delete query
        response = query.execute()

        # Check if the deletion was successful
        if not response.data:  # If no data is returned, no user was deleted
            raise HTTPException(status_code=404, detail="User not found or already deleted")

        return {"message": "User deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/movies")
def delete_movie(title: str, movie_id: int):
    try:
        # Delete movie by ID and Title
        response = supabase.table("movies").delete().eq("id", movie_id).eq("title", title).execute()
        
        # Check if any data was deleted by inspecting the response data
        if not response.data:  # If no data is returned, movie is not found or already deleted
            raise HTTPException(status_code=404, detail="Movie not found or already deleted")
        
        return {"message": "Movie deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))