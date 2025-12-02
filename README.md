Project Ingress — Automated Dataset Builder  
Version: 1.0  
Author: Aidan Robertson  
Course: CMP400 – Honours Project  
University: Abertay University  

Overview

Project Ingress is a web-based tool designed to automatically transform messy or semi-structured data sources (CSV, JSON, HTML pages, and later PDFs) into clean, analysable datasets.

The system provides:
- A FastAPI backend for ingesting and processing data  
- A React frontend for uploading files/URLs and previewing output  
- A core workflow following Ingest > Preview > Export

This is the Feasibility Demonstration release (v1.0), showing that the core architecture and workflow are functional and achievable within the project timeline.

Features Implemented in v1.0

Backend (FastAPI)
GET /health — confirms backend availability  
POST /ingest — accepts CSV files or URL input  
             — Reads CSV data  
             — Returns structured JSON preview  
POST /export — accepts data payload and returns exportable file  

The backend currently supports CSV ingestion with HTML and PDF parsing planned for later releases.

Frontend (React)
- File upload interface (CSV)  
- Sends files to backend /ingest 
- Displays returned JSON preview  
- URL input field (placeholder functionality)  
- Export button (stub or functional depending on backend state)

This demonstrates the end-to-end flow:  
Frontend > Backend > Frontend

Architecture

project-ingress/
│
├── backend/             FastAPI application
│   ├── main.py
│   ├── routers/
│   ├── models/
│   └── ...
│
├── frontend/            React UI
│   ├── src/
│   ├── public/
│   └── package.json

Getting Started

Prerequisites
- Python 3.10+
- Node.js + npm
- Git

Backend Setup

Navigate to the backend folder:

cd backend

Install dependencies:

pip install requirements.txt

Run FastAPI:

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
uvicorn main:app --reload

The API will be available at:

- http://127.0.0.1:8000  
- Swagger docs: http://127.0.0.1:8000/docs

Frontend Setup

Navigate to the frontend folder:

cd ingress-frontend

Install React dependencies:

npm install

Run the frontend:

npm start

Frontend runs at:

- http://localhost:3000

 Testing the Workflow

1. Start FastAPI
2. Open /docs and test /health
3. Upload a CSV via /ingest to see a JSON preview  
4. Open the React app and upload the same CSV  
5. Verify preview displays properly  
6. Test the export function  

This confirms the technical feasibility of the entire ingestion pipeline.

Known Limitations (v1.0)

- HTML table extraction incomplete  
- PDF parsing not implemented  
- Data Book generation not implemented  
- UI is an early functional prototype  

These features will be added in later releases.
