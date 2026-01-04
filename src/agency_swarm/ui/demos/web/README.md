# Agency Swarm Web UI

A complete web interface for Agency Swarm with all the features of the terminal UI, plus modern web capabilities.

## Features

### Chat Features
- ✅ Real-time streaming responses (SSE)
- ✅ Multi-agent communication with handoffs
- ✅ Agent mention syntax (@agent)
- ✅ Markdown rendering with syntax highlighting
- ✅ Reasoning display toggle
- ✅ Function call visualization
- ✅ Cancel streaming (ESC button)

### Commands
- ✅ `/help` - Show available commands
- ✅ `/new` - Start new chat
- ✅ `/compact [instructions]` - Summarize and continue
- ✅ `/resume` - Resume previous conversation
- ✅ `/status` - Show agency status
- ✅ `/cost` - Show usage and costs

### Persistence
- ✅ Chat history in sidebar
- ✅ Auto-save after each message
- ✅ Chat metadata (summary, timestamps, branch)
- ✅ Usage tracking per chat

### UI/UX
- ✅ Modern dark theme
- ✅ Responsive design
- ✅ Keyboard shortcuts (Ctrl+K, Ctrl+/)
- ✅ Auto-resize textarea
- ✅ Usage panel with cost breakdown
- ✅ Agent selector dropdown

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                         │
│  (React + TypeScript + Tailwind CSS)                         │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │ Chat UI     │  │ Sidebar     │  │ Commands    │        │
│  │ Components  │  │ Components  │  │ Components  │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
│         ↓                  ↓                  ↓             │
│  ┌───────────────────────────────────────────────────┐    │
│  │              API Routes (Next.js)                  │    │
│  │  /api/chat, /api/chats, /api/agents, /api/command  │    │
│  └───────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              ↓ HTTP/SSE
┌─────────────────────────────────────────────────────────────┐
│                    Python Backend (FastAPI)                  │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Agency Swarm Integration                │   │
│  │  - Multi-agent orchestration                        │   │
│  │  - Streaming responses                              │   │
│  │  - Chat persistence                                 │   │
│  │  - Usage tracking                                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

**Frontend (Node.js):**
```bash
cd agency-swarm/src/agency_swarm/ui/demos/web
npm install
```

**Backend (Python):**
```bash
cd agency-swarm/src/agency_swarm/ui/demos/web/backend
pip install -r requirements.txt
```

### 2. Configure Your Agency

Edit `backend/main.py` to set up your agents:

```python
def create_agency() -> Agency:
    ceo = Agent(
        name="CEO",
        description="Agency coordinator",
        instructions="...",
        model="gpt-4o-mini",
    )

    developer = Agent(
        name="Developer",
        description="Code specialist",
        instructions="...",
        model="gpt-4o-mini",
    )

    return Agency(
        agents=[ceo, developer],
        default_agent=ceo,
    )
```

### 3. Run the Backend

```bash
cd backend
python main.py
# Server runs on http://localhost:8000
```

### 4. Run the Frontend

In a new terminal:

```bash
cd web
npm run dev
# UI runs on http://localhost:3000
```

### 5. Open in Browser

Navigate to `http://localhost:3000`

## Environment Variables

Create a `.env.local` file in the web directory:

```bash
# Python backend URL
PYTHON_BACKEND_URL=http://localhost:8000

# Optional: Custom chats directory
AGENCY_SWARM_CHATS_DIR=./chats
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Open command menu |
| `Ctrl+/` | Focus chat input |
| `Enter` | Send message |
| `Shift+Enter` | New line in input |
| `ESC` | Cancel streaming / Close modals |

## Project Structure

```
web/
├── app/
│   ├── api/           # API routes (bridge to Python backend)
│   │   ├── chat/
│   │   ├── chats/
│   │   ├── agents/
│   │   └── command/
│   ├── globals.css    # Global styles
│   ├── layout.tsx     # Root layout
│   └── page.tsx       # Main chat page
├── components/        # React components
│   ├── ChatContainer.tsx
│   ├── InputArea.tsx
│   ├── Sidebar.tsx
│   ├── CommandMenu.tsx
│   ├── UsagePanel.tsx
│   └── AgentSelector.tsx
├── hooks/            # Custom React hooks
│   ├── useChat.ts
│   └── useChats.ts
├── types/            # TypeScript types
│   └── index.ts
├── utils/            # Utility functions
│   └── format.ts
├── package.json
└── tsconfig.json

backend/
├── main.py           # FastAPI server
└── requirements.txt
```

## Development

### Adding New Commands

1. Add command to `types/index.ts` SlashCommand type
2. Add command definition to `components/CommandMenu.tsx`
3. Handle command in `backend/main.py` execute_command()
4. Update frontend hook if needed

### Adding New UI Components

Components use Tailwind CSS for styling. Follow the existing patterns:

- Use `className` for styling
- Prefer semantic HTML
- Include TypeScript types
- Export as default

## Deployment

### Frontend (Vercel)

```bash
npm run build
vercel deploy
```

### Backend (Any Python host)

Set `PYTHON_BACKEND_URL` environment variable to your backend URL.

## Troubleshooting

**CORS errors:**
- Ensure backend is running
- Check PYTHON_BACKEND_URL is correct
- Verify CORS middleware in backend

**Chat not saving:**
- Check AGENCY_SWARM_CHATS_DIR is writable
- Verify backend permissions

**Streaming not working:**
- Check browser console for errors
- Verify backend is returning SSE headers
- Try disabling browser extensions

## License

MIT - Same as Agency Swarm
