"""
Insurance Claim Chatbot - FastAPI Backend
Simple demo/POC with in-memory sessions and JSON file storage
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import uuid
import json
from datetime import datetime
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Import agent and chatbot logic
from chatbot import ChatbotManager
from agent import StrandsAgent

app = FastAPI(title="Insurance Claim Chatbot API")

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Hardcoded users array with policies
USERS = [
    {
        "name": "Demo User One",
        "email": "demo1@company.com",
        "password": "demo123",
        "policies": [
            {
                "policyNumber": "POL-2024-001",
                "type": "Auto Insurance",
                "status": "Active",
                "premium": "$1,200/year",
                "coverage": "Full Coverage",
                "vehicle": "2020 Toyota Camry",
                "expiryDate": "2024-12-31"
            },
            {
                "policyNumber": "POL-2024-002",
                "type": "Home Insurance",
                "status": "Active",
                "premium": "$800/year",
                "coverage": "Comprehensive",
                "property": "123 Main St, City",
                "expiryDate": "2024-11-30"
            },
            {
                "policyNumber": "POL-2026-003",
                "type": "Bike Insurance",
                "status": "Active",
                "premium": "$120/year",
                "coverage": "Comprehensive",
                "property": "123 Main St, City",
                "expiryDate": "2026-12-31"
            }
        ]
    },
    {
        "name": "Demo User Two",
        "email": "demo2@company.com",
        "password": "demo456",
        "policies": [
            {
                "policyNumber": "POL-2024-003",
                "type": "Auto Insurance",
                "status": "Active",
                "premium": "$1,500/year",
                "coverage": "Full Coverage",
                "vehicle": "2022 Honda Accord",
                "expiryDate": "2025-01-15"
            }
        ]
    }
]

# In-memory session storage
# sessionId -> {user: {...}, chatbot_state: {...}}
sessions: Dict[str, Dict[str, Any]] = {}

# Data directory for JSON files (relative to backend directory)
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# Pydantic models
class LoginRequest(BaseModel):
    email: str
    password: str


class ChatRequest(BaseModel):
    message: str
    sessionId: str


class LogoutRequest(BaseModel):
    sessionId: str


class ChatResponse(BaseModel):
    response: str
    questionType: str  # "text", "yesno", "options"
    options: Optional[list] = None
    completed: bool = False


# Helper function to get session
def get_session(session_id: str) -> Dict[str, Any]:
    """Get session data or raise 401"""
    if session_id not in sessions:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")
    return sessions[session_id]


# Authentication endpoints
@app.post("/login")
async def login(credentials: LoginRequest):
    """Login with email and password"""
    # Find matching user
    user = None
    for u in USERS:
        if u["email"] == credentials.email and u["password"] == credentials.password:
            user = u
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create session
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "user": {
            "name": user["name"],
            "email": user["email"]
        },
        "policies": user.get("policies", []),
        "chatbot_state": None  # Will be initialized by ChatbotManager
    }
    
    # Initialize chatbot for this session (fresh start)
    chatbot_manager = ChatbotManager()
    sessions[session_id]["chatbot_state"] = chatbot_manager.get_state()
    
    return {
        "sessionId": session_id,
        "user": sessions[session_id]["user"],
        "policies": sessions[session_id]["policies"]
    }


@app.post("/logout")
async def logout(request: LogoutRequest):
    """Logout and clear session"""
    if request.sessionId in sessions:
        del sessions[request.sessionId]
    return {"message": "Logged out successfully"}


# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Handle chatbot conversation"""
    session = get_session(request.sessionId)
    user = session["user"]
    chatbot_state = session.get("chatbot_state")
    
    # Get or create chatbot manager
    chatbot_manager = ChatbotManager()
    
    # If message is 'reset', start completely fresh
    if request.message.lower() == 'reset':
        chatbot_manager = ChatbotManager()
        chatbot_state = chatbot_manager.get_state()
        session["chatbot_state"] = chatbot_state
    elif chatbot_state is None:
        # No state exists, start fresh
        chatbot_state = chatbot_manager.get_state()
        session["chatbot_state"] = chatbot_state
    else:
        # Restore existing state
        chatbot_manager.set_state(chatbot_state)
    
    # Check if policy number is being entered and get policy data
    policy_data = None
    if chatbot_state:
        current_step = chatbot_state.get("current_step", 0)
        # First question (step 0) is policy number
        if current_step == 0 and request.message and len(request.message.strip()) > 3:
            # Try to find matching policy
            policies = session.get("policies", [])
            policy_data = next((p for p in policies if request.message.strip().upper() in p["policyNumber"].upper()), None)
    else:
        # New session, check if first message is a policy number
        if request.message and len(request.message.strip()) > 3:
            policies = session.get("policies", [])
            policy_data = next((p for p in policies if request.message.strip().upper() in p["policyNumber"].upper()), None)
    
    # Process user message with available policies for validation
    policies = session.get("policies", [])
    response_data = await chatbot_manager.process_message(request.message, user, policy_data, policies)
    
    # Update session state
    session["chatbot_state"] = chatbot_manager.get_state()
    
    # If claim is completed, save to JSON file and reset state for next time
    if response_data.get("completed", False):
        save_claim_data(user, chatbot_manager.get_fnol_data())
        # Reset chatbot state for next conversation
        chatbot_manager = ChatbotManager()
        session["chatbot_state"] = chatbot_manager.get_state()
    
    return ChatResponse(
        response=response_data["response"],
        questionType=response_data["questionType"],
        options=response_data.get("options"),
        completed=response_data.get("completed", False)
    )


@app.get("/policies")
async def get_policies(sessionId: str):
    """Get policies for logged-in user"""
    session = get_session(sessionId)
    policies = session.get("policies", [])
    return {"policies": policies}


@app.get("/policy/{policy_number}")
async def get_policy(policy_number: str, sessionId: str):
    """Get specific policy details"""
    session = get_session(sessionId)
    policies = session.get("policies", [])
    
    policy = next((p for p in policies if p["policyNumber"].upper() == policy_number.upper()), None)
    
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    
    return {"policy": policy}


def save_claim_data(user: Dict[str, str], claim_data: Dict[str, Any]):
    """Save claim data to JSON file"""
    email_safe = user["email"].replace("@", "_").replace(".", "_")
    claim_file = DATA_DIR / f"{email_safe}.json"
    
    save_data = {
        "user": user,
        "submittedAt": datetime.now().isoformat(),
        "claimData": claim_data
    }
    
    with open(claim_file, "w") as f:
        json.dump(save_data, f, indent=2)


@app.get("/")
async def root():
    """Health check"""
    return {"message": "Insurance Claim Chatbot API", "status": "running"}

