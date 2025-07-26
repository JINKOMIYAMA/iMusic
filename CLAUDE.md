# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a YouTube M4A downloader PWA (Progressive Web App) that allows users to download YouTube videos as M4A files with embedded metadata and album art. The application consists of a React frontend and FastAPI backend, designed for Railway deployment.

## Architecture

**Monorepo Structure:**
- `frontend/` - React + TypeScript + Vite application with shadcn/ui components
- `backend/` - Python FastAPI server with yt-dlp integration
- Root level contains deployment scripts and configuration

**Key Components:**
- **Frontend**: PWA-enabled React app with service worker, installable on mobile devices
- **Backend**: FastAPI server handling YouTube downloads with FFmpeg audio processing
- **Deployment**: Dual Railway services (frontend + backend) with GitHub Actions CI/CD

## Development Commands

### Local Development
```bash
# Start full development environment (both frontend and backend)
./start_dev.sh

# Alternative simple start
./start.sh

# Production build and serve
./start_prod.sh
```

### Frontend (in frontend/ directory)
```bash
npm run dev          # Start Vite development server
npm run build        # Production build
npm run build:dev    # Development build
npm run lint         # ESLint code checking
npm run preview      # Preview production build
npm run serve        # Serve built files
```

### Backend (in backend/ directory)
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python app.py

# Debug FFmpeg availability
curl http://localhost:8000/debug/ffmpeg
```

### Testing and Quality
- **Frontend**: Uses ESLint for code quality (`npm run lint`)
- **Backend**: No specific test framework configured
- **Integration**: Test via start scripts that verify both services

## Key Technical Details

### Backend FFmpeg Integration
The application includes sophisticated FFmpeg path detection for Railway/Nixpacks environments:
- Searches multiple paths including Nix store locations
- Falls back to direct M4A download if FFmpeg unavailable
- Critical for audio format conversion and metadata embedding

### PWA Configuration
- Service worker at `frontend/public/sw.js`
- Web app manifest for mobile installation
- Install prompt component for user engagement

### Railway Deployment
- Separate railway.toml configs for frontend and backend services
- Environment variables for API URLs and authentication
- Automatic GitHub Actions deployment on push

### Authentication
- Basic Auth protection for the application
- Configured via environment variables

## Environment Setup

### Required Environment Variables

**Backend (.env in backend/):**
```
BASIC_AUTH_USERNAME=your_username
BASIC_AUTH_PASSWORD=your_password
```

**Frontend (.env in frontend/):**
```
VITE_API_BASE_URL=http://localhost:8000  # Development
# VITE_API_BASE_URL=https://your-backend.railway.app  # Production
```

### Dependencies
- **System**: Python 3.8+, Node.js 18+, FFmpeg (optional but recommended)
- **Python**: FastAPI, yt-dlp, Pillow, mutagen, uvicorn
- **Node.js**: React, TypeScript, Vite, Tailwind CSS, shadcn/ui

## Important File Locations

- `backend/app.py` - Main FastAPI application with download endpoints
- `frontend/src/pages/Index.tsx` - Main application page
- `frontend/src/components/InstallPWA.tsx` - PWA installation component
- `backend/downloads/` - Temporary file storage (cleaned automatically)
- `frontend/public/manifest.json` - PWA manifest
- `.github/workflows/` - CI/CD automation

## Development Notes

- The application primarily handles single video downloads (playlists have limited support)
- Sophisticated metadata parsing from video titles and uploader information
- Thumbnail processing to 800x800 album art with image enhancement
- CORS configured for cross-origin development
- Automatic cleanup of old downloaded files (24-hour retention)

## Debugging

Use the debug endpoint to troubleshoot FFmpeg issues:
```bash
curl http://localhost:8000/debug/ffmpeg
```

This endpoint provides detailed information about FFmpeg availability and search paths.