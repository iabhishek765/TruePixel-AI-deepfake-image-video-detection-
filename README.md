# TruePixel AI - Deepfake & Synthetic Image Detection

> 🤝 This is a collaborative project built with my teammate 
> [Arpit](https://github.com/Arpit-hue-max).
> Original repo: [TruePixel AI](https://github.com/Arpit-hue-max/TruePixel-AI-deepfake-image-video-detection-)

TruePixel AI is a premium web application designed to detect AI-generated, synthetic, and deepfaked images with high precision. It uses an **ensemble approach** combining a modern Swin Transformer model with a CNN-equivalent frequency-domain spectral analysis tool.

---

## 📂 Project Directory Structure

We have organized the repository files to be clean, modular, and easily accessible:

```
├── backend/
│   ├── Dockerfile                 # Docker configuration for backend FastAPI service
│   ├── server.py                  # API endpoints, DB wrapper, and model pipeline logic
│   ├── preload_model.py           # Script to download and cache classification weights
│   ├── requirements.txt           # Python backend dependencies
│   ├── truepixel_local.db         # SQLite local fallback database (persisted)
│   └── storage_local/             # Local upload folder for images (persisted)
│
├── frontend/
│   ├── Dockerfile                 # Docker configuration for React frontend service
│   ├── package.json               # Node dependencies and scripts
│   ├── craco.config.js            # Tailwind & CRA overrides config
│   ├── tailwind.config.js         # Styling tokens and theme configuration
│   └── src/
│       ├── App.js                 # App routing and React application shell
│       ├── index.js               # Application entry point
│       ├── pages/
│       │   ├── Dashboard.jsx      # Core dashboard, dropzones, and analysis result visualizers
│       │   └── LoginPage.jsx      # Register/login interface with glowing animations
│       └── components/            # UI components and primitives
│
├── tests/
│   └── __init__.py                # Tests package descriptor
├── backend_test.py                # Legacy basic integration tests
├── improved_backend_test.py       # Comprehensive integration test suite (Pillow generated tests)
├── image_testing.md               # Integration playbook for visual feature handling
├── auth_testing.md                # Testing playbooks for register/login flows
├── docker-compose.yml             # Root orchestrator to start the full stack instantly
└── README.md                      # Developer documentation and manual (this file)
```

---

## 🐳 Running with Docker (Recommended)

Docker Compose is configured to launch the complete stack. The backend Dockerfile preloads the model weights at build time, so there are no loading delays when starting the server.

### 1. Build and Start the Containers
Open a terminal in the root folder and run:
```bash
docker-compose up --build
```

### 2. Access the Application
- **Frontend User Interface**: Open [http://localhost:3000](http://localhost:3000) in your web browser.
- **Backend FastAPI Swagger Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs).

*Note: Database modifications and uploaded images will persist inside `./backend/truepixel_local.db` and `./backend/storage_local/` respectively.*

---

## 💻 Running Locally

If you prefer to run the applications directly on your machine without Docker:

### 1. Run the Backend
1. Go to the `backend` folder:
   ```bash
   cd backend
   ```
2. Install Python requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Preload the model weights:
   ```bash
   python preload_model.py
   ```
4. Start the server:
   ```bash
   python -m uvicorn server:app --host 127.0.0.1 --port 8000
   ```

### 2. Run the Frontend
1. Open a new terminal and go to the `frontend` folder:
   ```bash
   cd frontend
   ```
2. Install Node packages:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm start
   ```

---

## 🧪 Running Integration Tests

Ensure your backend server is running on `http://localhost:8000`. In the root folder, run:

```bash
# On Windows PowerShell
$env:PYTHONIOENCODING='utf-8'; python improved_backend_test.py

# On macOS/Linux
PYTHONIOENCODING=utf-8 python improved_backend_test.py
```
This runs 7/7 backend checks including health checks, token registration, protected route authorization, image upload, Swin Transformer inference, and session termination.
