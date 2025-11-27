<div align="center">

<img src="./Logo.png" alt="InStoryBook Logo" width="200"/>

# InStoryBook

**AI-powered children's storybook generator using multi-agent collaboration**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![LangChain](https://img.shields.io/badge/LangChain-0.3+-1C3C3C.svg)](https://www.langchain.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D.svg)](https://redis.io/)
[![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF.svg)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg)](https://tailwindcss.com/)
[![Node.js](https://img.shields.io/badge/Node.js-20+-339933.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://www.docker.com/)
[![WebSocket](https://img.shields.io/badge/WebSocket-Enabled-010101.svg)](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

Generate beautiful children's storybooks with AI-powered text and illustrations through intelligent multi-agent workflows.

</div>

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Redis (via Docker)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Instorybook
```

2. Configure environment variables:
```bash
cp env.example .env
# Edit .env with your API keys
```

3. Start all services:
```bash
./start.sh
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

5. Stop all services:
```bash
./stop.sh
```

## Environment Configuration

Copy `env.example` to `.env` and configure the following:

### Required API Keys

```bash
# Redis (local development uses Docker)
REDIS_URL=redis://localhost:6379/0

# AWS / Nova (Amazon Bedrock)
AWS_ACCESS_KEY=your_aws_access_key
AWS_SECRET_KEY=your_aws_secret_key
AWS_REGION=us-east-1
NOVA_MODEL=us.amazon.nova-lite-v1:0

# OpenAI (Fallback)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# Runware (Image Generation)
RUNWARE_API_KEY=your_runware_api_key
RUNWARE_IMAGE_MODEL=runware:101@1
RUNWARE_API_BASE_URL=https://api.runware.ai/v1

# AI Provider
AI_PROVIDER=nova
AI_FALLBACK_PROVIDER=openai

# Frontend (Build-time)
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1/ws

# CORS
CORS_ORIGINS=http://localhost:5173

# Debug
DEBUG=false
```

## Scripts

### Start Services (`./start.sh`)

Starts all services in the correct order:
1. Redis (Docker container)
2. Backend (FastAPI on port 8000)
3. Frontend (Vite dev server on port 5173)

Logs are saved to `logs/` directory.

### Stop Services (`./stop.sh`)

Stops all services:
1. Frontend service
2. Backend service
3. Redis (optional, prompts for confirmation)

## Requirements

### Backend Requirements

- Python 3.11+
- FastAPI 0.115+
- LangGraph 0.2+
- Redis 7.0+
- See `backend/requirements.txt` for full list

### Frontend Requirements

- Node.js 20+
- React 18+
- TypeScript 5.0+
- See `frontend/package.json` for full list

### AI Services

- Amazon Bedrock (Nova model) - Primary text generation
- OpenAI (GPT-4o-mini) - Fallback text generation
- Runware - Image generation

## Project Structure

```
Instorybook/
├── backend/                          # Backend service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application entry
│   │   ├── agents/                   # LangGraph agents
│   │   │   ├── __init__.py
│   │   │   ├── state.py              # LangGraph state definition
│   │   │   ├── conversation/         # Conversation layer
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py         # Router agent (intent recognition)
│   │   │   │   └── chat.py           # Chat agent (conversation)
│   │   │   └── workflow/             # Workflow layer
│   │   │       ├── __init__.py
│   │   │       ├── graph.py          # LangGraph workflow definition
│   │   │       ├── planner.py        # Planner agent (story planning)
│   │   │       ├── writer.py         # Writer agents (×4, parallel)
│   │   │       ├── illustrator.py    # Illustrator agents (×4, parallel)
│   │   │       └── finalizer.py      # Finalizer agents (text + image)
│   │   ├── api/                      # API routes
│   │   │   ├── __init__.py
│   │   │   ├── websocket.py          # WebSocket endpoint
│   │   │   └── story.py              # Story generation handler
│   │   ├── core/                     # Core configuration
│   │   │   ├── config.py             # Application settings
│   │   │   └── redis.py              # Redis client
│   │   ├── models/                   # Data models
│   │   │   └── schemas.py            # Pydantic schemas
│   │   ├── services/                 # Service layer
│   │   │   └── ai_services/          # AI service abstraction
│   │   │       ├── __init__.py
│   │   │       ├── text_generator.py # Text generation (Nova/OpenAI)
│   │   │       └── image_generator.py # Image generation (Runware)
│   │   └── utils/                    # Utilities
│   │       ├── __init__.py
│   │       └── json_utils.py         # JSON extraction utilities
│   ├── tests/                        # Test suite
│   │   ├── unit/                     # Unit tests
│   │   │   ├── agents/               # Agent tests
│   │   │   ├── test_config.py
│   │   │   ├── test_redis.py
│   │   │   ├── test_schemas.py
│   │   │   ├── test_text_generator.py
│   │   │   └── test_image_generator.py
│   │   ├── integration/              # Integration tests
│   │   │   ├── test_ai_services_integration.py
│   │   │   ├── test_multi_turn_conversation.py
│   │   │   ├── test_router_integration.py
│   │   │   └── test_story_websocket_integration.py
│   │   └── e2e/                      # End-to-end tests
│   ├── Dockerfile                    # Docker configuration
│   ├── requirements.txt              # Python dependencies
│   └── pytest.ini                    # Pytest configuration
│
├── frontend/                         # Frontend service
│   ├── src/
│   │   ├── main.tsx                  # React entry point
│   │   ├── App.tsx                   # Main app component
│   │   ├── index.css                 # Global styles
│   │   ├── vite-env.d.ts             # Vite type definitions
│   │   ├── components/               # React components
│   │   │   ├── ChatInterface.tsx     # Main chat interface
│   │   │   ├── Layout.tsx            # App layout
│   │   │   ├── Sidebar.tsx            # Sidebar component
│   │   │   └── StoryDisplay/         # Story display component
│   │   │       └── index.tsx
│   │   ├── pages/                    # Page components
│   │   │   ├── Home/                 # Home page
│   │   │   │   └── index.tsx
│   │   │   └── Generate/            # Generation page
│   │   │       └── index.tsx
│   │   ├── stores/                   # State management (Zustand)
│   │   │   └── chatStore.ts          # Chat state store
│   │   ├── hooks/                    # Custom React hooks
│   │   │   └── useWebSocket.ts       # WebSocket hook
│   │   └── config/                   # Configuration
│   │       └── api.ts                # API configuration
│   ├── tests/                        # Test suite
│   │   ├── components/               # Component tests
│   │   ├── hooks/                    # Hook tests
│   │   ├── pages/                    # Page tests
│   │   ├── stores/                   # Store tests
│   │   └── integration/              # Integration tests
│   ├── public/                       # Static assets
│   ├── package.json                  # Node dependencies
│   ├── tsconfig.json                 # TypeScript config
│   ├── vite.config.ts                # Vite configuration
│   └── tailwind.config.js            # Tailwind CSS config
│
├── docs/                             # Documentation
│   └── PROJECT_DOCUMENTATION.md      # Detailed project docs
│
├── logs/                             # Application logs
│
├── docker-compose.yml                # Local development (Redis only)
├── docker-compose.prod.yml           # Production reference
├── vercel.json                       # Vercel deployment config
├── start.sh                          # Start all services
├── stop.sh                           # Stop all services
├── env.example                       # Environment variables template
└── README.md                         # This file
```

## Architecture

### System Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│    React + TypeScript + Vite            │
└──────────────────┬──────────────────────┘
                   │
                   │ HTTP + WebSocket
                   │
┌──────────────────▼──────────────────────┐
│      API Gateway (FastAPI)              │
│      WebSocket-first architecture       │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼
    │              │              │
┌───▼───┐    ┌─────▼─────┐
│ Redis │    │ LangGraph │
└───────┘    └───────────┘
```

### Agent Architecture (LangGraph Level-3)

**Top-level Router Flow:**

```
User Input
    │
    ▼
Router Agent (Conversation System)
    │
    ├─ 1. Update Memory Summary (incremental)
    ├─ 2. Intent Recognition
    │
    ├─ intent = "chat" ──────────────────────→ Chat Agent
    │                                             │
    │                                             ├─ Generate response
    │                                             ├─ Update Memory Summary
    │                                             └─ END (no workflow)
    │
    ├─ intent = "story_generate" ───────────→ Story Graph
    │   │                                         │
    │   ├─ Clear all story fields                ├─ Planner Agent
    │   └─ Pass Summary to Planner              │   │
    │                                             │   ├─ Check: has outline?
    │                                             │   │   ├─ Yes → Skip planning
    │                                             │   │   └─ No → Input validation
    │                                             │   │       ├─ Incomplete → needs_info=True → END
    │                                             │   │       └─ Complete → Generate outline
    │                                             │   │
    │                                             │   └─ FanOut Writers (×4, parallel)
    │                                             │   └─ FanOut Illustrators (×4, parallel)
    │                                             │
    │                                             ├─ Completion Check
    │                                             │   ├─ All Writers done → FinalizerText
    │                                             │   └─ All Illustrators done → FinalizerImage
    │                                             │
    │                                             └─ END
    │
    └─ intent = "regenerate" ───────────────→ Story Graph
        │                                         │
        ├─ Keep: story_outline, language          ├─ Planner Agent
        ├─ Clear: chapters, completed_*          │   │
        └─ Pass Summary + Intent to Planner       │   ├─ Use "modify existing" template
                                                    │   └─ Update outline based on request
                                                    │
                                                    └─ Re-generate with modified outline
```

**Story Graph Workflow:**

```
Planner Agent
    │
    ├─ Input Validation
    │   ├─ needs_info = True → END (return missing_fields)
    │   └─ needs_info = False → Continue
    │
    ├─ Generate/Modify Story Outline
    │   └─ Include image_description for each chapter
    │
    └─ FanOut
        │
        ├─ Writer Agents (×4, parallel)
        │   ├─ Writer 1 (Chapter 1)
        │   ├─ Writer 2 (Chapter 2)
        │   ├─ Writer 3 (Chapter 3)
        │   └─ Writer 4 (Chapter 4)
        │
        └─ Illustrator Agents (×4, parallel)
            ├─ Illustrator 1 (Chapter 1)
            ├─ Illustrator 2 (Chapter 2)
            ├─ Illustrator 3 (Chapter 3)
            └─ Illustrator 4 (Chapter 4)
        │
        ▼
    Completion Check
        │
        ├─ All Writers Complete? → FinalizerText
        │   └─ Merge & optimize all chapters
        │
        └─ All Illustrators Complete? → FinalizerImage
            └─ Merge & sort all images
        │
        ▼
    END (Complete Story)
```

### Data Flow

**First-time Story Generation:**

```
1. User Input: "The Brave Little Rabbit"
   │
   ▼
2. Frontend generates session_id (crypto.randomUUID())
   │
   ▼
3. Frontend establishes WebSocket: ws://localhost:8000/api/v1/ws/{session_id}
   │
   ▼
4. Frontend sends message: {"type": "message", "theme": "The Brave Little Rabbit"}
   │
   ▼
5. Backend receives message
   │
   ▼
6. Router Agent
   │   ├─ Load state from Redis (if exists)
   │   ├─ Update Memory Summary (incremental)
   │   └─ Intent Recognition → "story_generate"
   │
   ▼
7. Prepare State
   │   ├─ Clear all story fields
   │   └─ Set theme, session_id, intent
   │
   ▼
8. Planner Agent
   │   ├─ Check: has story_outline? → No
   │   ├─ Input Validation
   │   │   ├─ Complete? → Yes
   │   │   └─ Generate story outline (4 chapters + image descriptions)
   │   └─ Save to Redis
   │
   ▼
9. Story Graph Execution
   │   ├─ FanOut Writers (×4, parallel)
   │   │   ├─ Writer 1 → Chapter 1 text
   │   │   ├─ Writer 2 → Chapter 2 text
   │   │   ├─ Writer 3 → Chapter 3 text
   │   │   └─ Writer 4 → Chapter 4 text
   │   │
   │   ├─ FanOut Illustrators (×4, parallel)
   │   │   ├─ Illustrator 1 → Chapter 1 image
   │   │   ├─ Illustrator 2 → Chapter 2 image
   │   │   ├─ Illustrator 3 → Chapter 3 image
   │   │   └─ Illustrator 4 → Chapter 4 image
   │   │
   │   ├─ Completion Check
   │   │   ├─ All Writers done → FinalizerText
   │   │   │   └─ Merge & optimize story
   │   │   └─ All Illustrators done → FinalizerImage
   │   │       └─ Merge & sort images
   │   │
   │   └─ Real-time WebSocket events:
   │       ├─ agent_started (planner, writers, illustrators)
   │       ├─ finalizer_text (complete chapters)
   │       ├─ finalizer_image (complete images)
   │       └─ pipeline_completed
   │
   ▼
10. Frontend receives events
    │   ├─ Display pipeline visualization
    │   ├─ Stream text output
    │   ├─ Load images asynchronously
    │   └─ Show complete storybook
    │
    ▼
11. User can download PDF
```

**Regenerate Story (Multi-turn):**

```
1. User Input: "Change the main character to a kitten"
   │
   ▼
2. Frontend uses same session_id
   │
   ▼
3. Frontend sends via WebSocket
   │
   ▼
4. Backend loads state from Redis
   │   └─ Contains: story_outline, chapters, memory_summary
   │
   ▼
5. Router Agent
   │   ├─ Update Memory Summary (incremental)
   │   └─ Intent Recognition → "regenerate"
   │
   ▼
6. Prepare State
   │   ├─ Keep: story_outline, language, memory_summary
   │   └─ Clear: chapters, completed_writers, completed_image_gens
   │
   ▼
7. Planner Agent
   │   ├─ Check: has story_outline? → Yes
   │   ├─ Use "modify existing story" template
   │   ├─ Provide existing outline as context
   │   └─ Modify outline based on user request
   │
   ▼
8. Story Graph Execution (with modified outline)
   │   └─ Re-generate all chapters and images
   │
   ▼
9. Real-time updates via WebSocket
   │
   ▼
10. Frontend displays updated story
```

**Chat Flow (No Story Generation):**

```
1. User Input: "Nice weather today"
   │
   ▼
2. Router Agent
   │   ├─ Update Memory Summary
   │   └─ Intent Recognition → "chat"
   │
   ▼
3. Chat Agent
   │   ├─ Use Memory Summary + conversation history
   │   ├─ Generate friendly response
   │   └─ Update Memory Summary (include assistant reply)
   │
   ▼
4. WebSocket: chat_response event
   │
   ▼
5. Frontend displays chat message
   │
   └─ END (no story generation)
```

**Needs Information Flow:**

```
1. User Input: "Write a story" (incomplete - missing theme/details)
   │
   ▼
2. Router Agent → "story_generate"
   │
   ▼
3. Planner Agent
   │   ├─ Input Validation
   │   └─ Missing fields detected
   │
   ▼
4. Planner returns: needs_info = True
   │   ├─ missing_fields: ["theme", "characters"]
   │   └─ suggestions: ["Please provide a story theme"]
   │
   ▼
5. WebSocket: needs_info event
   │
   ▼
6. Frontend displays form
   │   └─ Ask user to provide missing information
   │
   ▼
7. User provides additional info
   │
   ▼
8. Process continues with complete input
```

### Key Components

#### Router Agent
- Memory management (incremental summary)
- Intent recognition (story_generate, regenerate, chat)
- Task routing

#### Planner Agent
- Story outline generation
- Input validation
- Language detection

#### Writer Agents (×4)
- Parallel chapter text generation
- Stream output support

#### Illustrator Agents (×4)
- Parallel image generation
- Based on planner's image descriptions

#### Finalizer Agents
- Text finalizer: Merge and optimize story
- Image finalizer: Merge and sort images

## Technology Stack

### Backend
- **FastAPI**: Web framework
- **LangGraph**: Agent orchestration
- **LangChain**: LLM abstraction
- **Redis**: State storage
- **WebSocket**: Real-time communication

### Frontend
- **React**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **Zustand**: State management
- **Tailwind CSS**: Styling

### AI Services
- **Amazon Bedrock (Nova)**: Primary text generation
- **OpenAI**: Fallback text & image generation
- **Runware**: Image generation

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

## Deployment

For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

- **Backend**: Railway (Docker)
- **Frontend**: Vercel
- **Redis**: Upstash
