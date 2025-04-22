from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import sqlite3
from datetime import datetime
import torch
import os
import logging
import uvicorn

from backend import StoryGenerator
from backend.utils import QualityChecker, log_memory_usage, clear_gpu_memory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Bedtime Story Generator API",
    description="API for generating bedtime stories using TinyLlama fine-tuned on TinyStories",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://napnapstat.azurewebsites.net"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Available themes and genres
AVAILABLE_THEMES = [
    "animals", "friendship", "family", "space", "ocean",
    "forest", "magic", "seasons", "weather", "toys"
]

AVAILABLE_GENRES = [
    "adventure", "fantasy", "mystery", "educational",
    "funny", "bedtime", "fairy tale", "fable"
]

# Database configuration
DB_PATH = "stories.db"

# Initialize utilities
quality_checker = QualityChecker()

# -------------------- DATABASE FUNCTIONS --------------------

def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS stories (
        id TEXT PRIMARY KEY,
        theme TEXT NOT NULL,
        genre TEXT NOT NULL,
        content TEXT NOT NULL,
        title TEXT NOT NULL,
        quality_score INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def get_db_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def save_story(story_id, theme, genre, content, title, quality_score):
    """Save a generated story to the database."""
    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO stories (id, theme, genre, content, title, quality_score) VALUES (?, ?, ?, ?, ?, ?)",
            (story_id, theme, genre, content, title, quality_score)
        )
        conn.commit()

        # Get the created timestamp
        cursor = conn.execute("SELECT created_at FROM stories WHERE id = ?", (story_id,))
        created_at = cursor.fetchone()["created_at"]

        return created_at

def get_stories(limit=10):
    """Get previously generated stories."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT id, theme, genre, content, title, quality_score, created_at FROM stories ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        stories = [dict(row) for row in cursor.fetchall()]

        return stories

def get_story(story_id):
    """Get a specific story by ID."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT id, theme, genre, content, title, quality_score, created_at FROM stories WHERE id = ?",
            (story_id,)
        )
        story = cursor.fetchone()

        return dict(story) if story else None

# -------------------- MODELS --------------------

class StoryRequest(BaseModel):
    theme: str
    genre: str
    max_length: Optional[int] = 200
    temperature: Optional[float] = 0.5

class StoryResponse(BaseModel):
    id: str
    theme: str
    genre: str
    content: str
    title: str
    quality: Dict[str, Any]
    created_at: str

class ThemeGenreList(BaseModel):
    themes: List[str]
    genres: List[str]

# -------------------- DEPENDENCIES --------------------

# Story generator instance (lazy loading)
_generator = None

def get_generator():
    """Get or initialize the story generator."""
    global _generator
    if _generator is None:
        model_path = os.environ.get("MODEL_PATH", "/Users/abhishek/Desktop/Projects/StoryTime-A-Short-Story-Generator/tinyllama_1500stories_model/adapter_model.safetensors")
        logger.info(f"Initializing StoryGenerator with model path: {model_path}")
        _generator = StoryGenerator(model_path)

        # Log memory usage after initialization
        log_memory_usage()
    return _generator

# -------------------- API ENDPOINTS --------------------

@app.on_event("startup")
async def startup_event():
    """Initialize database and load model on startup."""
    init_db()
    logger.info("Database initialized")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/themes-genres", response_model=ThemeGenreList)
async def get_themes_and_genres():
    """Get available themes and genres."""
    return {"themes": AVAILABLE_THEMES, "genres": AVAILABLE_GENRES}

@app.post("/generate", response_model=StoryResponse)
async def generate_story(request: StoryRequest, generator=Depends(get_generator)):
    """Generate a new bedtime story based on theme and genre."""
    # Validate theme and genre
    if request.theme not in AVAILABLE_THEMES:
        raise HTTPException(status_code=400, detail=f"Theme must be one of: {', '.join(AVAILABLE_THEMES)}")

    if request.genre not in AVAILABLE_GENRES:
        raise HTTPException(status_code=400, detail=f"Genre must be one of: {', '.join(AVAILABLE_GENRES)}")

    try:
        # Generate story using our modular generator
        story_content = generator.generate_story(
            theme=request.theme,
            genre=request.genre,
            max_length=request.max_length,
            temperature=request.temperature
        )

        # Generate title
        title = generator.generate_title(story_content)

        # Check story quality
        quality = generator.evaluate_quality(story_content)

        # Create unique ID for the story
        story_id = str(uuid.uuid4())

        # Save to database
        created_at = save_story(
            story_id,
            request.theme,
            request.genre,
            story_content,
            title,
            quality["score"]
        )

        # Return the response
        return {
            "id": story_id,
            "theme": request.theme,
            "genre": request.genre,
            "content": story_content,
            "title": title,
            "quality": quality,
            "created_at": created_at
        }

    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating story: {str(e)}")

@app.get("/stories", response_model=List[StoryResponse])
async def get_stored_stories(limit: int = 10):
    """Get previously generated stories."""
    try:
        stories = get_stories(limit)
        return stories
    except Exception as e:
        logger.error(f"Error fetching stories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stories: {str(e)}")

@app.get("/stories/{story_id}", response_model=StoryResponse)
async def get_stored_story(story_id: str):
    """Get a specific story by ID."""
    try:
        story = get_story(story_id)
        if story is None:
            raise HTTPException(status_code=404, detail="Story not found")
        return story
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching story: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching story: {str(e)}")

@app.get("/memory-stats")
async def get_memory_stats():
    """Get current memory usage statistics."""
    try:
        # Import memory utils to get stats
        from backend.utils.memory_utils import get_memory_usage

        # Get memory stats
        memory_stats = get_memory_usage()

        return {
            "memory_stats": memory_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting memory stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting memory stats: {str(e)}")

@app.post("/clear-memory")
async def clear_memory():
    """Clear memory to free up resources."""
    try:
        # Clear GPU memory
        clear_gpu_memory()

        return {
            "status": "success",
            "message": "Memory cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing memory: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing memory: {str(e)}")

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
