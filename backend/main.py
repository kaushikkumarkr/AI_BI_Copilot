# file: backend/main.py
# Load environment variables FIRST
from dotenv import load_dotenv
load_dotenv()  # Loads from .env in project root

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import os
import shutil
import logging


# Import utils
from backend.utils.logger import setup_logger

# Initialize Logger
logger = setup_logger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="AI Business Intelligence Copilot",
    description="Production-ready AI BI System with Multi-Agent Reasoning",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Models ---
class AnalysisRequest(BaseModel):
    task_id: str
    analysis_type: str = "full"
    report_type: str = "pdf"

class QueryRequest(BaseModel):
    query: str
    context_id: Optional[str] = None

class SQLRequest(BaseModel):
    query: str
    dataset_id: str

class FeedbackRequest(BaseModel):
    task_id: str
    rating: bool  # True = Up, False = Down
    comment: Optional[str] = None

# --- Routes ---

@app.get("/")
async def root():
    return {"message": "AI BI Copilot Backend is Running 🚀"}

# Import workflow
from backend.graph.workflow import app_workflow

async def run_workflow(task_id: str, file_path: str):
    """Execute the LangGraph workflow."""
    logger.info(f"Starting workflow for {task_id}")
    try:
        # Initial state
        initial_state = {
            "file_path": file_path,
            "task_id": task_id,
            "df": None,
            "summary": {},
            "quality_report": {},
            "statistics": {},
            "visualizations": {},
            "forecast": {},
            "final_report": {}
        }
        
        # Run graph
        # app_workflow.invoke is synchronous, but we are in async function.
        # For production, might want to run in threadpool if it blocks too much.
        # Since nodes are async, we should use ainvoke if available or just invoke.
        # LangGraph compile() returns a CompiledGraph which has ainvoke.
        result = await app_workflow.ainvoke(initial_state)
        
        logger.info(f"Workflow completed for {task_id}")
        # In a real app, we would persist 'result' to a database here.
        # For this demo, we'll just log it.
        
    except Exception as e:
        logger.error(f"Workflow failed for {task_id}: {e}")

@app.post("/analyze_dataset")
async def analyze_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    analysis_type: str = "full",
    report_type: str = "pdf"
):
    """
    Upload a dataset and start the multi-agent analysis workflow.
    """
    task_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{task_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File uploaded: {file.filename} (Task ID: {task_id})")
        
        # Trigger Workflow
        background_tasks.add_task(run_workflow, task_id, file_path)
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Analysis started successfully."
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed.")

# Import Agents
from backend.agents.sql_agent import SQLAgent
from backend.agents.semantic_query_agent import SemanticQueryAgent
from backend.agents.data_interpreter import DataInterpreter

# Initialize Agents (Global for now, or per request)
sql_agent = SQLAgent()
semantic_agent = SemanticQueryAgent()
interpreter = DataInterpreter()

def get_file_path(task_id: str) -> str:
    # Find file starting with task_id in uploads
    for f in os.listdir(UPLOAD_DIR):
        if f.startswith(task_id):
            return os.path.join(UPLOAD_DIR, f)
    return None

@app.post("/semantic_query")
async def semantic_query(request: QueryRequest):
    """
    Handle free-form natural language queries about the data.
    """
    if not request.context_id:
        return {"error": "Context ID (Task ID) is required."}
        
    file_path = get_file_path(request.context_id)
    if not file_path:
        return {"error": "Dataset not found."}
        
    # Load DF (In prod, use cache)
    df = interpreter.load_data(file_path)
    
    result = await semantic_agent.answer_query(df, request.query)
    return result

@app.post("/sql_query")
async def sql_query(request: SQLRequest):
    """
    Convert NL to SQL and execute.
    """
    file_path = get_file_path(request.dataset_id)
    if not file_path:
        return {"error": "Dataset not found."}
        
    # Load DF
    df = interpreter.load_data(file_path)
    
    result = await sql_agent.execute_query(df, request.query)
    return result

@app.get("/status/{task_id}")
async def get_status(task_id: str):
    """
    Get the progress of the analysis agents.
    """
    # TODO: Fetch state from SQLite/LangGraph
    return {"task_id": task_id, "status": "processing", "progress": 0.2, "current_agent": "Data Interpreter"}

@app.get("/charts/{task_id}")
async def get_charts(task_id: str):
    """
    Retrieve generated charts.
    """
    # TODO: Fetch images from storage
    return {"charts": []}

@app.get("/report/{task_id}")
async def get_report(task_id: str):
    """
    Download the final report.
    """
    # TODO: Return PDF or Markdown
    return {"report_url": f"/downloads/{task_id}_report.pdf"}

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Collect user feedback.
    """
    logger.info(f"Feedback received for {request.task_id}: {request.rating}")
    return {"message": "Feedback recorded."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# end file
