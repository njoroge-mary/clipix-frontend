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

# Caption generator will be initialized after environment is loaded
caption_generator = None

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
    global client, db, caption_generator
    
    # Startup
    try:
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ['DB_NAME']]
        
        # Test the connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Initialize caption generator
        caption_generator = CaptionGenerator()
        logger.info("Caption generator initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
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

# Video Editor Models
class VideoInfo(BaseModel):
    video_id: str
    filename: str
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    has_audio: bool
    file_size: int
    thumbnail_url: Optional[str] = None
    uploaded_at: datetime

class TrimRequest(BaseModel):
    video_id: str
    start_time: float
    end_time: float

class CutSegment(BaseModel):
    start: float
    end: float

class CutRequest(BaseModel):
    video_id: str
    segments: List[CutSegment]

class CaptionRequest(BaseModel):
    video_id: str
    language: Optional[str] = None

class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: float
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

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


# ==================== VIDEO EDITOR ENDPOINTS ====================

@api_router.post("/video/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video file for editing (max 10GB)"""
    try:
        # Validate file type
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed_extensions}")
        
        # Generate unique video ID
        video_id = str(uuid.uuid4())
        safe_filename = f"{video_id}{file_ext}"
        file_path = UPLOAD_DIR / safe_filename
        
        # Save uploaded file
        logger.info(f"Uploading video: {file.filename} ({file.size} bytes)")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get video information
        video_info = video_processor.get_video_info(str(file_path))
        
        # Generate thumbnail
        thumbnail_filename = f"{video_id}_thumb.jpg"
        thumbnail_path = video_processor.get_thumbnail(
            str(file_path), 
            video_info['duration'] / 2,  # Middle of video
            thumbnail_filename
        )
        
        # Save to database
        video_doc = {
            'video_id': video_id,
            'filename': file.filename,
            'stored_filename': safe_filename,
            'duration': video_info['duration'],
            'width': video_info['width'],
            'height': video_info['height'],
            'fps': video_info['fps'],
            'codec': video_info['codec'],
            'has_audio': video_info['has_audio'],
            'file_size': video_info['file_size'],
            'thumbnail_filename': thumbnail_filename,
            'uploaded_at': datetime.now(timezone.utc).isoformat()
        }
        
        await db.videos.insert_one(video_doc)
        
        logger.info(f"Video uploaded successfully: {video_id}")
        return {
            'video_id': video_id,
            'filename': file.filename,
            'duration': video_info['duration'],
            'width': video_info['width'],
            'height': video_info['height'],
            'file_size': video_info['file_size'],
            'thumbnail_url': f"/api/video/{video_id}/thumbnail"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading video: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@api_router.get("/video/{video_id}/info")
async def get_video_info(video_id: str):
    """Get video information"""
    try:
        video_doc = await db.videos.find_one({'video_id': video_id}, {'_id': 0})
        if not video_doc:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return video_doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/video/{video_id}/stream")
async def stream_video(video_id: str):
    """Stream video file"""
    try:
        video_doc = await db.videos.find_one({'video_id': video_id})
        if not video_doc:
            raise HTTPException(status_code=404, detail="Video not found")
        
        video_path = UPLOAD_DIR / video_doc['stored_filename']
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        return FileResponse(video_path, media_type="video/mp4")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/video/{video_id}/thumbnail")
async def get_thumbnail(video_id: str):
    """Get video thumbnail"""
    try:
        video_doc = await db.videos.find_one({'video_id': video_id})
        if not video_doc:
            raise HTTPException(status_code=404, detail="Video not found")
        
        thumbnail_path = UPLOAD_DIR / video_doc['thumbnail_filename']
        if not thumbnail_path.exists():
            raise HTTPException(status_code=404, detail="Thumbnail not found")
        
        return FileResponse(thumbnail_path, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting thumbnail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_trim_job(job_id: str, video_id: str, start_time: float, end_time: float):
    """Background task for trimming video"""
    try:
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['progress'] = 0.1
        
        # Get video info
        video_doc = await db.videos.find_one({'video_id': video_id})
        if not video_doc:
            raise Exception("Video not found")
        
        input_path = str(UPLOAD_DIR / video_doc['stored_filename'])
        output_filename = f"{video_id}_trimmed_{uuid.uuid4()}.mp4"
        
        processing_jobs[job_id]['progress'] = 0.3
        
        # Trim video
        output_path = video_processor.trim_video(input_path, start_time, end_time, output_filename)
        
        processing_jobs[job_id]['progress'] = 0.9
        
        # Save result
        result_id = str(uuid.uuid4())
        await db.processed_videos.insert_one({
            'result_id': result_id,
            'original_video_id': video_id,
            'operation': 'trim',
            'output_filename': output_filename,
            'parameters': {'start_time': start_time, 'end_time': end_time},
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 1.0
        processing_jobs[job_id]['result'] = {
            'result_id': result_id,
            'download_url': f"/api/video/download/{result_id}"
        }
        
    except Exception as e:
        logger.error(f"Trim job failed: {e}")
        processing_jobs[job_id]['status'] = 'failed'
        processing_jobs[job_id]['error'] = str(e)


@api_router.post("/video/trim")
async def trim_video(request: TrimRequest, background_tasks: BackgroundTasks):
    """Trim video between start and end time"""
    try:
        # Create job
        job_id = str(uuid.uuid4())
        processing_jobs[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'progress': 0.0,
            'message': 'Trim job queued',
            'result': None,
            'error': None
        }
        
        # Start background task
        background_tasks.add_task(
            process_trim_job,
            job_id,
            request.video_id,
            request.start_time,
            request.end_time
        )
        
        return {'job_id': job_id, 'status': 'pending'}
    
    except Exception as e:
        logger.error(f"Error starting trim job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_cut_job(job_id: str, video_id: str, segments: List[Dict]):
    """Background task for cutting video"""
    try:
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['progress'] = 0.1
        
        # Get video info
        video_doc = await db.videos.find_one({'video_id': video_id})
        if not video_doc:
            raise Exception("Video not found")
        
        input_path = str(UPLOAD_DIR / video_doc['stored_filename'])
        output_filename = f"{video_id}_cut_{uuid.uuid4()}.mp4"
        
        processing_jobs[job_id]['progress'] = 0.3
        
        # Cut video
        output_path = video_processor.cut_video(input_path, segments, output_filename)
        
        processing_jobs[job_id]['progress'] = 0.9
        
        # Save result
        result_id = str(uuid.uuid4())
        await db.processed_videos.insert_one({
            'result_id': result_id,
            'original_video_id': video_id,
            'operation': 'cut',
            'output_filename': output_filename,
            'parameters': {'segments': segments},
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 1.0
        processing_jobs[job_id]['result'] = {
            'result_id': result_id,
            'download_url': f"/api/video/download/{result_id}"
        }
        
    except Exception as e:
        logger.error(f"Cut job failed: {e}")
        processing_jobs[job_id]['status'] = 'failed'
        processing_jobs[job_id]['error'] = str(e)


@api_router.post("/video/cut")
async def cut_video(request: CutRequest, background_tasks: BackgroundTasks):
    """Cut video into segments and merge"""
    try:
        # Create job
        job_id = str(uuid.uuid4())
        processing_jobs[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'progress': 0.0,
            'message': 'Cut job queued',
            'result': None,
            'error': None
        }
        
        # Convert Pydantic models to dicts
        segments = [{'start': seg.start, 'end': seg.end} for seg in request.segments]
        
        # Start background task
        background_tasks.add_task(
            process_cut_job,
            job_id,
            request.video_id,
            segments
        )
        
        return {'job_id': job_id, 'status': 'pending'}
    
    except Exception as e:
        logger.error(f"Error starting cut job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_caption_job(job_id: str, video_id: str, language: Optional[str]):
    """Background task for generating captions"""
    try:
        processing_jobs[job_id]['status'] = 'processing'
        processing_jobs[job_id]['progress'] = 0.1
        processing_jobs[job_id]['message'] = 'Extracting audio...'
        
        # Get video info
        video_doc = await db.videos.find_one({'video_id': video_id})
        if not video_doc:
            raise Exception("Video not found")
        
        video_path = str(UPLOAD_DIR / video_doc['stored_filename'])
        
        # Extract audio
        audio_filename = f"{video_id}_audio.mp3"
        audio_path = video_processor.extract_audio(video_path, audio_filename)
        
        processing_jobs[job_id]['progress'] = 0.3
        processing_jobs[job_id]['message'] = 'Transcribing audio...'
        
        # Generate captions
        captions = await caption_generator.generate_captions(audio_path, language)
        
        processing_jobs[job_id]['progress'] = 0.8
        processing_jobs[job_id]['message'] = 'Generating subtitle files...'
        
        # Generate SRT and VTT files
        srt_filename = f"{video_id}_captions.srt"
        vtt_filename = f"{video_id}_captions.vtt"
        
        srt_path = str(UPLOAD_DIR / srt_filename)
        vtt_path = str(UPLOAD_DIR / vtt_filename)
        
        caption_generator.generate_srt(captions['segments'], srt_path)
        caption_generator.generate_vtt(captions['segments'], vtt_path)
        
        # Save to database
        caption_id = str(uuid.uuid4())
        await db.captions.insert_one({
            'caption_id': caption_id,
            'video_id': video_id,
            'text': captions['text'],
            'language': captions.get('language', language),
            'segments': captions['segments'],
            'srt_filename': srt_filename,
            'vtt_filename': vtt_filename,
            'created_at': datetime.now(timezone.utc).isoformat()
        })
        
        # Clean up audio file
        os.remove(audio_path)
        
        processing_jobs[job_id]['status'] = 'completed'
        processing_jobs[job_id]['progress'] = 1.0
        processing_jobs[job_id]['message'] = 'Captions generated successfully'
        processing_jobs[job_id]['result'] = {
            'caption_id': caption_id,
            'text': captions['text'],
            'language': captions.get('language', language),
            'segments': captions['segments'],
            'srt_url': f"/api/captions/{caption_id}/srt",
            'vtt_url': f"/api/captions/{caption_id}/vtt"
        }
        
    except Exception as e:
        logger.error(f"Caption job failed: {e}")
        processing_jobs[job_id]['status'] = 'failed'
        processing_jobs[job_id]['error'] = str(e)
        processing_jobs[job_id]['message'] = f'Failed: {str(e)}'


@api_router.post("/video/captions")
async def generate_captions(request: CaptionRequest, background_tasks: BackgroundTasks):
    """Generate AI captions for video"""
    try:
        # Create job
        job_id = str(uuid.uuid4())
        processing_jobs[job_id] = {
            'job_id': job_id,
            'status': 'pending',
            'progress': 0.0,
            'message': 'Caption generation queued',
            'result': None,
            'error': None
        }
        
        # Start background task
        background_tasks.add_task(
            process_caption_job,
            job_id,
            request.video_id,
            request.language
        )
        
        return {'job_id': job_id, 'status': 'pending'}
    
    except Exception as e:
        logger.error(f"Error starting caption job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get processing job status"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return processing_jobs[job_id]


@api_router.get("/video/download/{result_id}")
async def download_processed_video(result_id: str):
    """Download processed video"""
    try:
        result_doc = await db.processed_videos.find_one({'result_id': result_id})
        if not result_doc:
            raise HTTPException(status_code=404, detail="Processed video not found")
        
        video_path = UPLOAD_DIR / result_doc['output_filename']
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video file not found")
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=f"clipix_edited_{result_id}.mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/captions/{caption_id}/srt")
async def download_srt(caption_id: str):
    """Download SRT subtitle file"""
    try:
        caption_doc = await db.captions.find_one({'caption_id': caption_id})
        if not caption_doc:
            raise HTTPException(status_code=404, detail="Captions not found")
        
        srt_path = UPLOAD_DIR / caption_doc['srt_filename']
        if not srt_path.exists():
            raise HTTPException(status_code=404, detail="SRT file not found")
        
        return FileResponse(
            srt_path,
            media_type="application/x-subrip",
            filename=f"captions_{caption_id}.srt"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading SRT: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/captions/{caption_id}/vtt")
async def download_vtt(caption_id: str):
    """Download VTT subtitle file"""
    try:
        caption_doc = await db.captions.find_one({'caption_id': caption_id})
        if not caption_doc:
            raise HTTPException(status_code=404, detail="Captions not found")
        
        vtt_path = UPLOAD_DIR / caption_doc['vtt_filename']
        if not vtt_path.exists():
            raise HTTPException(status_code=404, detail="VTT file not found")
        
        return FileResponse(
            vtt_path,
            media_type="text/vtt",
            filename=f"captions_{caption_id}.vtt"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading VTT: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/videos")
async def list_videos():
    """List all uploaded videos"""
    try:
        videos = await db.videos.find({}, {'_id': 0}).to_list(100)
        return {'videos': videos, 'count': len(videos)}
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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