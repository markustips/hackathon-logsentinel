# Docker Setup Guide for LogSentinel AI

## Current Setup (SQLite - No Docker Needed!)

**Good News**: The current implementation uses **SQLite**, which stores the database in a simple file. You don't need Docker for the database!

The SQLite database file will be created automatically at: `logsentinel.db` in your backend directory when you first run the application.

### Quick Start (No Docker Required)

```bash
# Just run the backend
cd backend
uvicorn main:app --reload --port 8000
```

That's it! SQLite will create the database automatically.

---

## Option 1: Keep Using SQLite (Recommended for Hackathon)

**Pros:**
- ✅ Zero setup - no Docker needed
- ✅ Fast and lightweight
- ✅ Perfect for development and demos
- ✅ Database is just a file (easy backup)

**Current Configuration:**
```bash
DATABASE_URL=sqlite:///./logsentinel.db
```

**No action needed - it just works!**

---

## Option 2: Upgrade to PostgreSQL with Docker

If you want to use PostgreSQL instead (for production or larger datasets):

### Step 1: Start PostgreSQL Container

```bash
# Start just the PostgreSQL database
docker-compose up -d postgres

# Check it's running
docker ps
```

### Step 2: Install PostgreSQL Driver

```bash
pip install psycopg2-binary
```

### Step 3: Update Environment Variable

Edit your `.env` file:

```bash
# Change from:
DATABASE_URL=sqlite:///./logsentinel.db

# To:
DATABASE_URL=postgresql://logsentinel:logsentinel_password@localhost:5432/logsentinel
```

### Step 4: Run Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The database tables will be created automatically on first run!

---

## Option 3: Run Everything in Docker

If you want to run both backend and database in Docker:

### Step 1: Create .env file

```bash
echo "ANTHROPIC_API_KEY=your-key-here" > .env
```

### Step 2: Build and Start All Services

```bash
# Build and start everything
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### Step 3: Access the Application

- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Step 4: View Logs

```bash
# View backend logs
docker-compose logs -f backend

# View database logs
docker-compose logs -f postgres
```

### Step 5: Stop Services

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (deletes data!)
docker-compose down -v
```

---

## Docker Commands Reference

### Managing Containers

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# Restart services
docker-compose restart

# Remove containers (keeps data)
docker-compose down

# Remove everything including data
docker-compose down -v

# View running containers
docker ps

# View all containers
docker ps -a
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100
```

### Accessing Container Shell

```bash
# Backend container
docker exec -it logsentinel-backend bash

# Database container
docker exec -it logsentinel-db psql -U logsentinel -d logsentinel
```

### Database Operations

```bash
# Connect to PostgreSQL
docker exec -it logsentinel-db psql -U logsentinel -d logsentinel

# Backup database
docker exec logsentinel-db pg_dump -U logsentinel logsentinel > backup.sql

# Restore database
docker exec -i logsentinel-db psql -U logsentinel -d logsentinel < backup.sql

# View database size
docker exec -it logsentinel-db psql -U logsentinel -c "SELECT pg_size_pretty(pg_database_size('logsentinel'));"
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Port Already in Use

```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# On Windows, kill the process
taskkill /PID <process_id> /F

# Or change the port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Wait for health check
docker-compose ps
```

### Out of Disk Space

```bash
# Clean up unused Docker resources
docker system prune -a

# Remove old volumes
docker volume prune
```

---

## Data Persistence

### SQLite
- Database file: `backend/logsentinel.db`
- FAISS indices: `data/faiss_index/`
- Uploaded files: `data/uploads/`

**Backup SQLite:**
```bash
# Simple copy
cp backend/logsentinel.db backup_$(date +%Y%m%d).db

# Or use SQLite dump
sqlite3 backend/logsentinel.db .dump > backup.sql
```

### PostgreSQL with Docker
Data is stored in Docker volumes:
- `postgres_data`: Database files
- `faiss_data`: FAISS indices

**Backup PostgreSQL:**
```bash
# Backup
docker exec logsentinel-db pg_dump -U logsentinel logsentinel > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i logsentinel-db psql -U logsentinel -d logsentinel < backup.sql
```

---

## Performance Comparison

### SQLite (Current)
- **Speed**: Very fast for < 100k records
- **Concurrency**: Single writer
- **Setup**: Zero configuration
- **Best for**: Development, demos, small deployments

### PostgreSQL
- **Speed**: Scales to millions of records
- **Concurrency**: Multiple concurrent writers
- **Setup**: Requires Docker/installation
- **Best for**: Production, large datasets, multiple users

---

## Recommended Setup for Different Use Cases

### 1. Hackathon Demo (Next 24 hours)
**Use SQLite** - No Docker needed!
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 2. Local Development
**Use SQLite** - Fastest iteration
```bash
# SQLite for fast dev
DATABASE_URL=sqlite:///./logsentinel.db
```

### 3. Production Deployment
**Use PostgreSQL with Docker**
```bash
docker-compose up -d postgres
DATABASE_URL=postgresql://logsentinel:logsentinel_password@localhost:5432/logsentinel
```

### 4. Full Docker Deployment
**Use docker-compose for everything**
```bash
docker-compose up -d --build
```

---

## Current Status

✅ **SQLite is configured and ready to use**
✅ **No Docker required for the demo**
✅ **Database will be created automatically on first run**

Optional Docker files created:
- `docker-compose.yml` - Full Docker setup
- `docker-compose.simple.yml` - PostgreSQL only
- `backend/Dockerfile` - Backend container

**For your hackathon demo, just use SQLite - it works perfectly!**

---

## Quick Decision Guide

**Use SQLite if:**
- ✅ Doing a demo or hackathon
- ✅ < 100,000 log records
- ✅ Want zero setup time
- ✅ Single user access

**Use PostgreSQL if:**
- ✅ Production deployment
- ✅ > 100,000 log records
- ✅ Multiple concurrent users
- ✅ Need advanced SQL features

**For your current hackathon, SQLite is perfect!** 🚀
