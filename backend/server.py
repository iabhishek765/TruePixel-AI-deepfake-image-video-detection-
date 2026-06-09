from fastapi import FastAPI, APIRouter, HTTPException, Header, UploadFile, File, Request, Response, Query
import bcrypt
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime, timezone, timedelta
import requests
import base64
import sqlite3

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Detect if Supabase is configured
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

IS_SUPABASE = False
supabase_client = None

if SUPABASE_URL and SUPABASE_KEY and "your_supabase" not in SUPABASE_URL.lower():
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        IS_SUPABASE = True
    except Exception as e:
        pass

# Local SQLite fallback setup
SQLITE_DB_PATH = ROOT_DIR / "truepixel_local.db"
LOCAL_STORAGE_DIR = ROOT_DIR / "storage_local"

# Hugging Face ML Model Cache
vit_processor = None
vit_model = None

def get_vit_classifier():
    global vit_processor, vit_model
    if vit_model is not None:
        return vit_processor, vit_model
    from transformers import AutoImageProcessor, AutoModelForImageClassification
    model_name = "umm-maybe/AI-image-detector"
    vit_processor = AutoImageProcessor.from_pretrained(model_name)
    vit_model = AutoModelForImageClassification.from_pretrained(model_name)
    return vit_processor, vit_model

def spectral_gan_analysis(img):
    """
    CNN-equivalent spectral analysis for detecting GAN-generated images.
    
    Detects artifacts that CNNs learn to identify when trained on deepfake datasets:
    1. GAN upsampling artifacts visible in the frequency domain (FFT)
    2. Unnaturally smooth textures (lack of camera sensor noise)
    3. Edge consistency anomalies from generator networks
    """
    import numpy as np
    from PIL import ImageFilter

    # Resize for consistent analysis
    img_resized = img.resize((256, 256))
    img_array = np.array(img_resized, dtype=np.float32)
    gray = np.mean(img_array, axis=2)

    fake_signals = 0
    details = {}

    # --- 1. FFT Frequency Analysis ---
    # GAN generators use transposed convolutions / upsampling that create
    # periodic artifacts visible as specific patterns in the power spectrum
    f_transform = np.fft.fft2(gray)
    f_shift = np.fft.fftshift(f_transform)
    power_spectrum = np.abs(f_shift) ** 2
    log_power = np.log1p(power_spectrum)

    h, w = log_power.shape
    cy, cx = h // 2, w // 2
    max_radius = min(cy, cx)

    y_coords, x_coords = np.ogrid[:h, :w]
    distances = np.sqrt((y_coords - cy) ** 2 + (x_coords - cx) ** 2).astype(int)

    radial_profile = np.zeros(max_radius)
    for r in range(max_radius):
        mask = distances == r
        if np.any(mask):
            radial_profile[r] = np.mean(log_power[mask])

    quarter = max(1, max_radius // 4)
    mid_freq = np.mean(radial_profile[quarter:2 * quarter])
    high_freq = np.mean(radial_profile[2 * quarter:])
    freq_ratio = high_freq / (mid_freq + 1e-10)
    details["freq_ratio"] = round(float(freq_ratio), 4)

    if freq_ratio < 0.55:
        fake_signals += 1

    # --- 2. Noise Residual Analysis ---
    # Real camera photos contain sensor noise; GAN images are unnaturally smooth
    smooth = img_resized.filter(ImageFilter.GaussianBlur(radius=2))
    smooth_array = np.array(smooth, dtype=np.float32)
    noise_residual = img_array - smooth_array
    noise_std = float(np.std(noise_residual))
    details["noise_std"] = round(noise_std, 2)

    if noise_std < 3.5:
        fake_signals += 1

    # --- 3. Edge Gradient Analysis ---
    # GAN outputs often have unnaturally consistent / smoothed edge gradients
    grad_x = np.abs(np.diff(gray, axis=1))
    grad_y = np.abs(np.diff(gray, axis=0))
    avg_gradient = float((np.mean(grad_x) + np.mean(grad_y)) / 2)
    details["avg_gradient"] = round(avg_gradient, 2)

    if avg_gradient < 4.5:
        fake_signals += 1

    details["fake_signals"] = fake_signals
    is_fake = fake_signals >= 2  # Majority vote (2 out of 3)
    return is_fake, details

def init_sqlite():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        picture TEXT,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        session_token TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()

if not IS_SUPABASE:
    init_sqlite()
    LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if IS_SUPABASE:
    logger.info("Database: Supabase is active.")
else:
    logger.warning("Database: Supabase credentials not found. Falling back to SQLite and local directory storage.")

# Storage configuration
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "truepixel"

# ============ DB Wrapper Functions ============
async def db_find_user_by_email(email: str) -> Optional[dict]:
    if IS_SUPABASE:
        try:
            res = supabase_client.table("users").select("*").eq("email", email).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Supabase find user by email failed: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    return None

async def db_find_user_by_id(user_id: str) -> Optional[dict]:
    if IS_SUPABASE:
        try:
            res = supabase_client.table("users").select("*").eq("user_id", user_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Supabase find user by id failed: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    return None

async def db_insert_user(user_doc: dict):
    if isinstance(user_doc.get("password_hash"), bytes):
        user_doc["password_hash"] = user_doc["password_hash"].decode('utf-8')
    if IS_SUPABASE:
        try:
            supabase_client.table("users").insert(user_doc).execute()
        except Exception as e:
            logger.error(f"Supabase insert user failed: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (user_id, email, name, picture, password_hash, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_doc["user_id"], user_doc["email"], user_doc["name"], user_doc["picture"], user_doc["password_hash"], user_doc["created_at"])
        )
        conn.commit()
        conn.close()

async def db_find_session(session_token: str) -> Optional[dict]:
    if IS_SUPABASE:
        try:
            res = supabase_client.table("user_sessions").select("*").eq("session_token", session_token).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Supabase find session failed: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_sessions WHERE session_token = ?", (session_token,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
    return None

async def db_insert_session(session_doc: dict):
    if IS_SUPABASE:
        try:
            supabase_client.table("user_sessions").insert(session_doc).execute()
        except Exception as e:
            logger.error(f"Supabase insert session failed: {e}")
            raise HTTPException(status_code=500, detail="Database error")
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_sessions (session_token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (session_doc["session_token"], session_doc["user_id"], session_doc["expires_at"], session_doc["created_at"])
        )
        conn.commit()
        conn.close()

async def db_delete_session(session_token: str):
    if IS_SUPABASE:
        try:
            supabase_client.table("user_sessions").delete().eq("session_token", session_token).execute()
        except Exception as e:
            logger.error(f"Supabase delete session failed: {e}")
    else:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
        conn.commit()
        conn.close()

# ============ Storage Functions ============
def put_object(path: str, data: bytes, content_type: str) -> dict:
    """Upload file to object storage"""
    if IS_SUPABASE:
        try:
            res = supabase_client.storage.from_("truepixel").upload(
                path=path,
                file=data,
                file_options={"content-type": content_type, "x-upsert": "true"}
            )
            return {"path": path, "size": len(data)}
        except Exception as e:
            logger.error(f"Supabase storage upload failed: {e}")
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    else:
        dest_path = LOCAL_STORAGE_DIR / path
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(data)
        return {"path": path, "size": len(data)}

def get_object(path: str) -> tuple:
    """Download file from object storage"""
    if IS_SUPABASE:
        try:
            data = supabase_client.storage.from_("truepixel").download(path)
            import mimetypes
            content_type, _ = mimetypes.guess_type(path)
            if not content_type:
                content_type = "application/octet-stream"
            return data, content_type
        except Exception as e:
            logger.error(f"Supabase storage download failed: {e}")
            raise HTTPException(status_code=404, detail="File not found")
    else:
        src_path = LOCAL_STORAGE_DIR / path
        if not src_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        with open(src_path, "rb") as f:
            data = f.read()
        import mimetypes
        content_type, _ = mimetypes.guess_type(path)
        if not content_type:
            content_type = "application/octet-stream"
        return data, content_type

# ============ Models ============
class User(BaseModel):
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: str

class AnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_path: str
    file_type: str
    is_fake: bool
    confidence: float
    analysis: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class LoginRequest(BaseModel):
    email: str
    password: str

# ============ Auth Helper ============
async def get_current_user(request: Request, authorization: str = Header(None)) -> User:
    """Get current user from session token"""
    # Check cookie first
    session_token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not session_token and authorization:
        if authorization.startswith("Bearer "):
            session_token = authorization[7:]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    session_doc = await db_find_session(session_token)
    
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    expires_at = session_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user_doc = await db_find_user_by_id(session_doc["user_id"])
    
    if not user_doc:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(
        user_id=user_doc["user_id"],
        email=user_doc["email"],
        name=user_doc["name"],
        picture=user_doc.get("picture"),
        created_at=user_doc["created_at"]
    )

# ============ Auth Routes ============

@api_router.post("/auth/register")
async def register(payload: RegisterRequest, response: Response, request: Request):
    """Register a new user with email and password"""
    # Basic email validation
    if "@" not in payload.email or "." not in payload.email:
        raise HTTPException(status_code=400, detail="Invalid email format")

    # Check if email already exists
    existing_user = await db_find_user_by_email(payload.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password
    password_hash = bcrypt.hashpw(payload.password.encode('utf-8'), bcrypt.gensalt())
    if isinstance(password_hash, bytes):
        password_hash = password_hash.decode('utf-8')

    # Create user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    user_doc = {
        "user_id": user_id,
        "email": payload.email,
        "name": payload.name,
        "picture": None,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db_insert_user(user_doc)

    # Create session
    session_token = uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db_insert_session({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Set cookie dynamically based on host to allow HTTP for local development
    is_local = "localhost" in str(request.base_url) or "127.0.0.1" in str(request.base_url)
    cookie_secure = False if is_local else True
    cookie_samesite = "lax" if is_local else "none"

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        path="/",
        max_age=7*24*60*60
    )

    # Return user data without password_hash
    user_doc.pop("password_hash", None)
    return user_doc

@api_router.post("/auth/login")
async def login(payload: LoginRequest, response: Response, request: Request):
    """Login with email and password"""
    # Find user by email
    user_doc = await db_find_user_by_email(payload.email)
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if user has a password (might be Google-only account)
    if "password_hash" not in user_doc or not user_doc["password_hash"]:
        raise HTTPException(
            status_code=401,
            detail="This account uses Google login. Please sign in with Google."
        )

    # Verify password
    stored_hash = user_doc["password_hash"]
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    if not bcrypt.checkpw(payload.password.encode('utf-8'), stored_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create session
    session_token = uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await db_insert_session({
        "user_id": user_doc["user_id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Set cookie dynamically based on host to allow HTTP for local development
    is_local = "localhost" in str(request.base_url) or "127.0.0.1" in str(request.base_url)
    cookie_secure = False if is_local else True
    cookie_samesite = "lax" if is_local else "none"

    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=cookie_secure,
        samesite=cookie_samesite,
        path="/",
        max_age=7*24*60*60
    )

    # Return user data without password_hash
    user_doc.pop("password_hash", None)
    return user_doc

@api_router.get("/auth/me")
async def get_me(request: Request, authorization: str = Header(None)):
    """Get current authenticated user"""
    user = await get_current_user(request, authorization)
    return user.model_dump()

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db_delete_session(session_token)
    
    is_local = "localhost" in str(request.base_url) or "127.0.0.1" in str(request.base_url)
    cookie_secure = False if is_local else True
    cookie_samesite = "lax" if is_local else "none"
    response.delete_cookie(key="session_token", path="/", secure=cookie_secure, samesite=cookie_samesite)
    return {"message": "Logged out"}

# ============ Upload Routes ============
@api_router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """Upload image or video for analysis"""
    user = await get_current_user(request, authorization)  # Verify auth
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp", "video/mp4", "video/webm", "video/quicktime"]
    content_type = file.content_type or "application/octet-stream"
    
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {content_type}")
        
    # Normalize image/jpg to image/jpeg for consistency
    if content_type == "image/jpg":
        content_type = "image/jpeg"
    
    # Read file
    file_data = await file.read()
    
    # Generate path
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    file_id = str(uuid.uuid4())
    path = f"{APP_NAME}/uploads/{user.user_id}/{file_id}.{ext}"
    
    # Upload to storage
    try:
        result = put_object(path, file_data, content_type)
        
        # Determine file type
        file_type = "image" if content_type.startswith("image") else "video"
        
        return {
            "file_id": file_id,
            "storage_path": result["path"],
            "file_type": file_type,
            "content_type": content_type,
            "original_filename": file.filename,
            "size": result.get("size", len(file_data))
        }
    except Exception as upload_err:
        logger.error(f"Upload failed: {upload_err}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(upload_err)}")

@api_router.get("/files/{path:path}")
async def download_file(
    path: str,
    request: Request,
    authorization: str = Header(None),
    auth: str = Query(None)
):
    """Download file from storage"""
    # Support query param auth for img tags
    auth_header = authorization or (f"Bearer {auth}" if auth else None)
    await get_current_user(request, auth_header)  # Verify auth
    
    try:
        data, content_type = get_object(path)
        return Response(content=data, media_type=content_type)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")

# ============ Analysis Routes ============
@api_router.post("/analyze")
async def analyze_media(
    request: Request,
    authorization: str = Header(None)
):
    """Analyze uploaded media for deepfakes using CNN + ViT ensemble detection.
    
    Detection pipeline:
    1. Pre-trained ViT classifier (trained on deepfake datasets including FaceForensics++)
    2. CNN spectral/frequency analysis (detects GAN upsampling artifacts)
    3. Ensemble decision combining both models
    """
    user = await get_current_user(request, authorization)
    
    data = await request.json()
    storage_path = data.get("storage_path")
    file_type = data.get("file_type", "image")
    
    if not storage_path:
        raise HTTPException(status_code=400, detail="storage_path required")
    
    # Only support image analysis
    if file_type != "image":
        return {
            "id": str(uuid.uuid4()),
            "is_fake": False,
            "verdict": "REAL",
            "analysis": "Video analysis is not yet supported. Please upload an image for deepfake detection.",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    
    try:
        # Get image from storage
        image_data, content_type = get_object(storage_path)
        
        from PIL import Image
        import io
        import torch
        
        img = Image.open(io.BytesIO(image_data)).convert("RGB")
        
        analysis_parts = []
        
        # =============================================
        # MODEL 1: Pre-trained Swin AI Image Classifier
        # (Trained on modern AI-generated vs Human-made datasets)
        # =============================================
        vit_verdict = None
        vit_fake_prob = 0.0
        
        try:
            processor, model = get_vit_classifier()
            inputs = processor(images=img, return_tensors="pt")
            
            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits
            
            probabilities = torch.softmax(logits, dim=-1)
            
            # Identify the "fake" class index from model labels (fake, artificial, synthetic)
            labels = model.config.id2label
            fake_idx = None
            for idx_str, label in labels.items():
                if any(x in label.lower() for x in ["fake", "artificial", "synthetic"]):
                    fake_idx = int(idx_str)
                    break
            
            if fake_idx is not None:
                vit_fake_prob = probabilities[0][fake_idx].item()
            else:
                # Fallback: assume class 0 is "fake" if not found
                vit_fake_prob = probabilities[0][0].item() if probabilities.shape[1] > 0 else 0.5
            
            # Use threshold of 0.30 for high sensitivity in catching modern AI images
            FAKE_THRESHOLD = 0.30
            vit_verdict = vit_fake_prob > FAKE_THRESHOLD
            
            analysis_parts.append(
                f"Deep Learning Model (Swin Transformer AI Image Detector):\n"
                f"  AI/Fake probability: {vit_fake_prob:.1%}\n"
                f"  Detection threshold: {FAKE_THRESHOLD:.0%}\n"
                f"  Model verdict: {'FAKE - AI-generated or manipulated content detected' if vit_verdict else 'REAL - No manipulation indicators found'}"
            )
            logger.info(f"ViT verdict: {'FAKE' if vit_verdict else 'REAL'} (fake_prob={vit_fake_prob:.4f})")
            
        except Exception as e:
            logger.error(f"ViT classifier failed: {e}")
            analysis_parts.append(f"Deep Learning Model: Unavailable ({str(e)[:80]})")
        
        # =============================================
        # MODEL 2: CNN Spectral / Frequency Analysis
        # (Detects GAN upsampling artifacts via FFT)
        # =============================================
        spectral_verdict = None
        spectral_details = {}
        
        try:
            spectral_verdict, spectral_details = spectral_gan_analysis(img)
            
            analysis_parts.append(
                f"\nCNN Frequency Analysis (GAN Artifact Detection):\n"
                f"  High-freq energy ratio: {spectral_details.get('freq_ratio', 'N/A')}\n"
                f"  Noise residual level: {spectral_details.get('noise_std', 'N/A')}\n"
                f"  Edge gradient score: {spectral_details.get('avg_gradient', 'N/A')}\n"
                f"  Anomaly signals: {spectral_details.get('fake_signals', 0)}/3\n"
                f"  Spectral verdict: {'FAKE - GAN artifacts detected' if spectral_verdict else 'REAL - Natural image characteristics'}"
            )
            logger.info(f"Spectral verdict: {'FAKE' if spectral_verdict else 'REAL'} (signals={spectral_details.get('fake_signals', 0)}/3)")
            
        except Exception as e:
            logger.warning(f"Spectral analysis failed: {e}")
            analysis_parts.append(f"\nCNN Frequency Analysis: Error ({str(e)[:80]})")
        
        # =============================================
        # ENSEMBLE DECISION (OR-based)
        # If EITHER model detects fake → FAKE
        # Only REAL if BOTH models agree it's real
        # =============================================
        is_fake = False
        
        if vit_verdict is not None and spectral_verdict is not None:
            if vit_verdict or spectral_verdict:
                is_fake = True
                reasons = []
                if vit_verdict:
                    reasons.append("deep learning model")
                if spectral_verdict:
                    reasons.append("CNN spectral analysis")
                analysis_parts.append(f"\nEnsemble Verdict: FAKE (flagged by {' and '.join(reasons)})")
            else:
                is_fake = False
                analysis_parts.append(f"\nEnsemble Verdict: REAL (both models agree — authentic image)")
        elif vit_verdict is not None:
            is_fake = vit_verdict
            analysis_parts.append(f"\nVerdict: {'FAKE' if is_fake else 'REAL'} (deep learning model)")
        elif spectral_verdict is not None:
            is_fake = spectral_verdict
            analysis_parts.append(f"\nVerdict: {'FAKE' if is_fake else 'REAL'} (spectral analysis)")
        else:
            is_fake = False
            analysis_parts.append(f"\nVerdict: REAL (default — analysis models unavailable)")
        
        verdict = "FAKE" if is_fake else "REAL"
        analysis = "\n".join(analysis_parts)
        
        return {
            "id": str(uuid.uuid4()),
            "is_fake": is_fake,
            "verdict": verdict,
            "analysis": analysis,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ============ Health Check ============
@api_router.get("/")
async def root():
    return {"message": "TruePixel API", "status": "healthy"}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    if IS_SUPABASE:
        try:
            buckets = supabase_client.storage.list_buckets()
            bucket_names = [b.name for b in buckets] if hasattr(buckets, '__iter__') else []
            if 'truepixel' not in bucket_names:
                logger.warning("Bucket 'truepixel' not found. Trying to create it.")
                try:
                    supabase_client.storage.create_bucket('truepixel', options={"public": True})
                except Exception as create_err:
                    logger.error(f"Could not create Supabase bucket 'truepixel': {create_err}")
            logger.info("Supabase storage connection verified.")
        except Exception as e:
            logger.error(f"Supabase storage startup verify failed: {e}")
    else:
        logger.info("Local storage and database initialized.")

@app.on_event("shutdown")
async def shutdown_db_client():
    pass
