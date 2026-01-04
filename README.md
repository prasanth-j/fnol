# FNOL Vehicle Accident Chatbot

A simple end-to-end demo/POC for a First Notice of Loss (FNOL) Vehicle Accident Chatbot using Python FastAPI backend, React frontend, and Google Gemini AI.

## Features

- **Simple Authentication**: Hardcoded user array (no database)
- **AI-Powered Chatbot**: Uses Gemini 2.5 Flash for input understanding and normalization
- **Enterprise UI**: Dashboard with policy list and floating chatbot interface
- **Conversational Mode**: Chatbot starts in conversational mode, switches to FNOL when user mentions a claim
- **Policy Integration**: Automatic policy lookup when policy number is entered
- **Structured Question Flow**: Backend-controlled conversation with 19 questions
- **JSON Storage**: User-based FNOL data persistence in local files

## Tech Stack

- **Backend**: Python 3.8+ with FastAPI
- **AI Agent**: Strands Agents SDK with Google Gemini 2.5 Flash
- **Frontend**: React 18 with Bootstrap 5
- **Storage**: JSON files (no database)

## Project Structure

```
fnol/
├── backend/
│   ├── main.py          # FastAPI application
│   ├── chatbot.py       # Conversation flow controller
│   ├── agent.py         # Gemini AI agent for input processing
│   └── requirements.txt # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   └── components/
│   │       ├── LoginPage.js
│   │       ├── DashboardPage.js
│   │       ├── FloatingChatbot.js
│   │       ├── DashboardPage.css
│   │       └── FloatingChatbot.css
│   ├── public/
│   └── package.json
├── data/                # JSON files for FNOL storage (created automatically)
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note**: The `strands-agents` package will be installed as part of the dependencies. This is the official AWS Strands Agents SDK. The `[gemini]` extra includes Gemini model support.

4. Set your Gemini API key using a `.env` file:
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your-api-key-here
```

Alternatively, you can set it as an environment variable:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

On Windows:
```cmd
set GEMINI_API_KEY=your-api-key-here
```

**Note**: The application supports both `GEMINI_API_KEY` and `GOOGLE_API_KEY` environment variables. If both are set, `GOOGLE_API_KEY` takes precedence.

5. Start the FastAPI server:
```bash
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the React development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## Demo Credentials

The application includes two hardcoded demo users:

| Email | Password |
|-------|----------|
| demo1@company.com | demo123 |
| demo2@company.com | demo456 |

## Usage

1. **Login**: Use one of the demo credentials to log in
2. **View Policies**: After login, you'll see your policies listed on the dashboard
3. **Start Chat**: Click the floating chat button (bottom right) to start a conversation
4. **Conversational Mode**: The chatbot starts in conversational mode - chat normally until you mention a claim
5. **File a Claim**: When you mention keywords like "accident", "claim", "incident", the chatbot switches to FNOL mode
6. **Chatbot Flow**: Answer the 19 questions in sequence:
   - Policy Number
   - Contact Number
   - Incident Date & Time
   - Type of Incident (dropdown)
   - Location
   - Weather (dropdown)
   - Police Report (Yes/No)
   - Police Report Number (if Yes)
   - Vehicle Damage
   - Driveable (Yes/No)
   - Towing Required (Yes/No)
   - Photos Taken (Yes/No)
   - Injuries (dropdown)
   - Driver Name
   - Driver Relation (dropdown)
   - Driver License Number
   - Driving Experience (dropdown)
   - Driver Condition (Yes/No)
   - Consent (Yes/No)

3. **Policy Lookup**: When entering your policy number, the chatbot automatically shows your policy details
4. **Auto-Save**: FNOL data is automatically saved to JSON files upon completion
5. **Logout**: Click logout to end your session

## Question Flow Control

- **Backend Controls Flow**: The backend Python code determines which question to ask next
- **Strands Agent for Understanding**: The Strands framework with Gemini 2.5 Flash is used only to understand and normalize user input, not to decide questions
- **Constrained Agent**: The Strands Agent is configured with a system prompt that restricts it to input normalization only
- **State Management**: Conversation state is stored in-memory per session

## Data Storage

FNOL data is saved to JSON files in the `/data` directory:
- Filename format: `{email_safe}.json`
- Example: `demo1_company_com.json`
- Structure:
```json
{
  "user": {
    "name": "Demo User One",
    "email": "demo1@company.com"
  },
  "submittedAt": "2024-01-15T10:30:00",
  "fnolData": {
    "policyNumber": "...",
    "contactNumber": "...",
    ...
  }
}
```

## API Endpoints

- `POST /login` - Authenticate user
- `POST /logout` - End session
- `POST /chat` - Send message to chatbot
- `GET /policies` - Get all policies for logged-in user
- `GET /policy/{policy_number}` - Get specific policy details

## Development Notes

- **No Database**: All data stored in JSON files
- **In-Memory Sessions**: Sessions are stored in memory (lost on server restart)
- **No JWT/OAuth**: Simple session-based auth for demo purposes
- **Local Only**: Designed for local development/demo

## Troubleshooting

1. **Gemini API Error**: 
   - Make sure `GEMINI_API_KEY` is set in `.env` file or as environment variable
   - Check that the `.env` file is in the `backend/` directory
   - Verify your API key is valid at https://makersuite.google.com/app/apikey
2. **CORS Issues**: Backend is configured to allow `localhost:3000` and `localhost:5173`
3. **Port Conflicts**: Change ports in `uvicorn` command or `package.json` if needed
4. **Module Not Found**: Ensure you're in the correct directory and dependencies are installed
5. **.env File Not Loading**: Make sure `python-dotenv` is installed: `pip install python-dotenv`

## License

This is a demo/POC project for educational purposes.

