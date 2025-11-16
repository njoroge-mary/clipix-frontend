from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import shutil
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import asyncio
import json

# Import video processing modules
from video_processor import VideoProcessor
from caption_generator import CaptionGenerator


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize video processing
UPLOAD_DIR = ROOT_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
video_processor = VideoProcessor(str(UPLOAD_DIR))
caption_generator = CaptionGenerator()

# Store processing jobs in memory (in production, use Redis or DB)
processing_jobs: Dict[str, Dict[str, Any]] = {}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate required environment variables
required_env_vars = ['MONGO_URL', 'DB_NAME']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# MongoDB connection (will be initialized in lifespan)
client: Optional[AsyncIOMotorClient] = None
db = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    global client, db
    
    # Startup
    try:
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        # Test the connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    
    yield
    
    # Shutdown
    if client:
        client.close()
        logger.info("MongoDB connection closed")


# Create the main app with lifespan
app = FastAPI(
    title="Clipix API",
    description="Backend API for Clipix application",
    version="1.0.0",
    lifespan=lifespan
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Health check endpoint to verify service and database status"""
    try:
        # Check MongoDB connection
        if client is None or db is None:
            raise HTTPException(status_code=503, detail="Database not initialized")
        
        # Ping MongoDB
        await client.admin.command('ping')
        
        return {
            "status": "healthy",
            "service": "clipix-backend",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@api_router.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to Clipix API",
        "version": "1.0.0",
        "status": "running"
    }


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    """Create a new status check entry"""
    try:
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        status_dict = input.model_dump()
        status_obj = StatusCheck(**status_dict)
        
        # Convert to dict and serialize datetime to ISO string for MongoDB
        doc = status_obj.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        
        result = await db.status_checks.insert_one(doc)
        
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create status check")
        
        logger.info(f"Status check created for client: {input.client_name}")
        return status_obj
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating status check: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    """Retrieve all status check entries"""
    try:
        if db is None:
            raise HTTPException(status_code=503, detail="Database not available")
        
        # Exclude MongoDB's _id field from the query results
        status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
        
        # Convert ISO string timestamps back to datetime objects
        for check in status_checks:
            if isinstance(check['timestamp'], str):
                check['timestamp'] = datetime.fromisoformat(check['timestamp'])
        
        logger.info(f"Retrieved {len(status_checks)} status checks")
        return status_checks
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving status checks: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# CORS middleware configuration
cors_origins = os.environ.get('CORS_ORIGINS', '*')
origins_list = cors_origins.split(',') if cors_origins != '*' else ['*']

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)