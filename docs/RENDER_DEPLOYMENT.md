# LogSentinel AI - Render Deployment

## Render Deployment Guide

### Prerequisites
- Render account (https://render.com)
- GitHub repository (already set up)
- API keys for LLM services

### Backend Deployment (Web Service)

1. **Create Web Service on Render:**
   - Connect to GitHub repository: `markustips/hackathon-logsentinel`
   - Root directory: `backend`
   - Environment: `Docker`
   - Region: Choose closest to your users
   - Instance type: `Starter` (can upgrade later)

2. **Environment Variables (Required):**
   ```
   GOOGLE_API_KEY=your_gemini_api_key_here
   DATABASE_URL=postgresql://render_postgresql_url_here
   PYTHONPATH=/app
   PORT=10000
   LOG_LEVEL=INFO
   LLM_PROVIDER=gemini
   GEMINI_MODEL=gemini-2.0-flash-exp
   ```

3. **Build Command:** (Auto-detected from Dockerfile)
   ```
   docker build -t logsentinel-backend .
   ```

4. **Start Command:**
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Frontend Deployment (Static Site)

1. **Create Static Site on Render:**
   - Connect to same GitHub repository
   - Root directory: `frontend`
   - Environment: `Node`
   - Build command: `npm install && npm run build`
   - Publish directory: `dist`

2. **Environment Variables:**
   ```
   VITE_API_URL=https://your-backend-service.onrender.com/api
   ```

### Database Setup

1. **Create PostgreSQL Database:**
   - Add PostgreSQL service on Render
   - Copy connection string to backend environment variables

### Domain Configuration
- Backend: `https://logsentinel-backend.onrender.com`
- Frontend: `https://logsentinel-frontend.onrender.com`

### Cost Estimation
- Backend Web Service: $7/month (Starter)
- Frontend Static Site: Free
- PostgreSQL Database: $7/month (Starter)
- **Total: ~$14/month**

### Deployment Steps
1. Push code to GitHub (✅ Done)
2. Create Render services
3. Configure environment variables
4. Deploy and test
5. Update CORS settings with production URLs