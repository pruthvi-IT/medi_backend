# MediNote Backend  
FastAPI • PostgreSQL • AWS S3 (or MinIO for local) • Docker • Railway Deployment

A production-ready backend for the MediNote challenge.  
Supports audio chunk uploads via **presigned URLs**, session tracking, and chunk notifications.  
Fully Dockerized and **deployable to Railway with zero code changes**.

---

# 🚀 Features
- FastAPI backend with modular routing
- Audio upload using **presigned PUT URLs**
- Works with both:
  - **AWS S3** (production)
  - **MinIO** (local development)
- PostgreSQL (via SQLAlchemy)
- Fully containerized Docker build
- Auto-ready for Railway deployment (DATABASE_URL, env vars)
- Clean & extensible folder structure

---

# 📂 Project Structure
