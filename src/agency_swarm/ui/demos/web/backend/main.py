"""
Agency Swarm Web Backend

FastAPI server that bridges the Next.js frontend with the Agency Swarm framework.
Provides SSE streaming, chat persistence, and command execution.
"""

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator

import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Set

# Add agency_swarm to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agency_swarm import Agency, Agent
from agency_swarm.ui.demos.launcher import TerminalDemoLauncher
from agency_swarm.ui.demos.persistence import (
    list_chat_records,
    save_current_chat,
    load_chat,
    load_chat_metadata,
)
from agency_swarm.utils.usage_tracking import UsageStats, extract_usage_from_run_result, calculate_usage_with_cost
from agency_swarm.tools.concurrency_v2 import (
    get_global_concurrency_manager,
    DeadlockResolutionStrategy,
)
from backend.settings_manager import get_settings_manager, SettingsManager
import httpx

# ============================================================================
# Configuration
# ============================================================================

# TODO: Configure your agency here
# This is a placeholder - you should import your actual agency setup
def create_agency() -> Agency:
    """Create and configure the Agency instance."""
    # Example: Create a simple agency for demo
    ceo = Agent(
        name="CEO",
        description="Agency coordinator that manages tasks",
        instructions="You are the CEO. Coordinate tasks and delegate to other agents.",
        model="gpt-4o-mini",
    )

    developer = Agent(
        name="Developer",
        description="Handles coding and technical tasks",
        instructions="You are a Developer. Write code and solve technical problems.",
        model="gpt-4o-mini",
    )

    agency = Agency(
        agents=[ceo, developer],
        default_agent=ceo,
        shared_instructions="You are part of an AI agency.",
    )

    return agency


# Global agency instance
_agency: Agency | None = None
_current_chat_id: str | None = None
_session_usage: UsageStats | None = None


def get_agency() -> Agency:
    """Get or create the global agency instance."""
    global _agency
    if _agency is None:
        _agency = create_agency()
    return _agency


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(title="Agency Swarm Web Backend")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Request/Response Models
# ============================================================================

class SendMessageRequest(BaseModel):
    message: str
    recipient_agent: str | None = None
    chat_id: str | None = None


class CommandRequest(BaseModel):
    command: str
    args: list[str] | None = None


class NewChatRequest(BaseModel):
    chat_id: str | None = None


# ============================================================================
# Concurrency Models
# ============================================================================

class OverrideLockRequest(BaseModel):
    reason: str


class ResolveDeadlockRequest(BaseModel):
    cycle: List[str]
    strategy: str = "priority"  # priority, youngest, oldest, random, manual
    victim_lock_id: str | None = None


# ============================================================================
# Settings Models
# ============================================================================

class APIData(BaseModel):
    provider: str
    key: str
    validated: bool = False
    last_validated: str | None = None
    models: List[str] = []


class ModelConfig(BaseModel):
    default_model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2048
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class AgentModelOverride(BaseModel):
    agent_name: str
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None


class SettingsData(BaseModel):
    version: str
    created_at: str
    updated_at: str
    encryption: dict
    api_keys: dict
    model_config: ModelConfig
    agent_overrides: dict


class UnlockSettingsRequest(BaseModel):
    password: str


class ValidateKeyRequest(BaseModel):
    provider: str
    key: str


class ValidateKeyResponse(BaseModel):
    valid: bool
    provider: str
    message: str
    error: str | None = None
    models: List[str] = []


# ============================================================================
# WebSocket Connection Manager
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time concurrency updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_personal(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)


ws_manager = ConnectionManager()


def setup_concurrency_websocket():
    """Setup WebSocket event callback for concurrency updates."""
    manager = get_global_concurrency_manager()

    def event_callback(event: dict):
        """Forward concurrency events to WebSocket clients."""
        # This runs in a thread, need to schedule async broadcast
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast(event))
        except Exception:
            pass  # Event loop not available

    manager.register_event_callback(event_callback)


# ============================================================================
# API Routes
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/agents")
async def list_agents():
    """List all available agents."""
    agency = get_agency()
    agents = [
        {
            "name": agent.name,
            "description": getattr(agent, "description", ""),
            "instructions": getattr(agent, "instructions", ""),
            "model": getattr(agent, "model", ""),
        }
        for agent in agency.agents.values()
    ]
    return {
        "agents": agents,
        "entry_points": [a.name for a in agency.entry_points],
        "default_agent": agency.default_agent.name if agency.default_agent else None,
    }


@app.post("/chat")
async def chat(request: SendMessageRequest):
    """
    Send a message to the agency and stream the response.

    Returns Server-Sent Events (SSE) stream.
    """
    global _current_chat_id, _session_usage

    agency = get_agency()

    # Determine chat ID
    chat_id = request.chat_id or _current_chat_id
    if not chat_id:
        chat_id = TerminalDemoLauncher.generate_chat_id()
        _current_chat_id = chat_id
        agency.thread_manager.replace_messages([])

    # Set or validate chat ID
    _current_chat_id = chat_id

    async def stream_response() -> AsyncGenerator[str, None]:
        """Stream events to the frontend."""
        try:
            # Get the response stream
            response_stream = agency.get_response_stream(
                message=request.message,
                recipient_agent=request.recipient_agent,
                chat_id=chat_id,
            )

            async for event in response_stream:
                # Convert event to SSE format
                event_data = convert_event_to_sse(event, request.recipient_agent)
                if event_data:
                    yield f"data: {json.dumps(event_data)}\n\n"

            # Extract usage from final result
            final_result = response_stream.final_result if response_stream else None
            if final_result:
                run_usage = extract_usage_from_run_result(final_result)
                if run_usage:
                    run_usage = calculate_usage_with_cost(run_usage, run_result=final_result)
                    global _session_usage
                    if _session_usage:
                        _session_usage = _session_usage + run_usage
                    else:
                        _session_usage = run_usage

                    yield f"data: {json.dumps({'type': 'usage', 'data': _session_usage.__dict__})}\n\n"

            # Save chat
            save_current_chat(agency, chat_id, usage=_session_usage.__dict__ if _session_usage else None)

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        stream_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Chat-ID": chat_id,
        },
    )


@app.post("/command")
async def execute_command(request: CommandRequest):
    """Execute a slash command."""
    global _current_chat_id, _session_usage

    agency = get_agency()

    command = request.command.lower()
    args = request.args or []

    try:
        match command:
            case "new":
                chat_id = TerminalDemoLauncher.generate_chat_id()
                _current_chat_id = chat_id
                _session_usage = UsageStats()
                agency.thread_manager.replace_messages([])
                return {"chat_id": chat_id, "message": "Started new chat"}

            case "resume":
                if not args:
                    # List available chats
                    chats = list_chat_records()
                    return {"chats": chats}
                else:
                    # Resume specific chat
                    chat_id = args[0]
                    if load_chat(agency, chat_id):
                        _current_chat_id = chat_id
                        metadata = load_chat_metadata(chat_id)
                        if metadata and "usage" in metadata:
                            saved_usage = metadata["usage"]
                            _session_usage = UsageStats(**saved_usage)
                        else:
                            _session_usage = UsageStats()
                        return {
                            "chat_id": chat_id,
                            "message": f"Resumed chat {chat_id}",
                            "messages": agency.thread_manager.get_all_messages(),
                            "usage": _session_usage.__dict__ if _session_usage else None,
                        }
                    raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")

            case "compact":
                # Compact the current conversation
                if not _current_chat_id:
                    raise HTTPException(status_code=400, detail="No active chat to compact")

                from agency_swarm.ui.demos.compact import compact_thread
                summary_msg = await compact_thread(agency, args)
                new_chat_id = TerminalDemoLauncher.generate_chat_id()
                agency.thread_manager.replace_messages([summary_msg])
                _current_chat_id = new_chat_id
                return {
                    "chat_id": new_chat_id,
                    "summary": summary_msg,
                    "message": "Conversation compacted",
                }

            case "status":
                return {
                    "agency": {
                        "name": getattr(agency, "name", "Agency Swarm"),
                        "agents": list(agency.agents.keys()),
                        "entry_points": [a.name for a in agency.entry_points],
                    },
                    "current_chat": _current_chat_id,
                    "cwd": os.getcwd(),
                }

            case "cost":
                return {
                    "usage": _session_usage.__dict__ if _session_usage else None,
                    "message": "Usage statistics",
                }

            case "help":
                return {
                    "commands": [
                        {"name": "help", "description": "Show this help"},
                        {"name": "new", "description": "Start a new chat"},
                        {"name": "compact [instructions]", "description": "Summarize and continue"},
                        {"name": "resume [chat_id]", "description": "Resume a chat"},
                        {"name": "status", "description": "Show status"},
                        {"name": "cost", "description": "Show usage and costs"},
                    ]
                }

            case _:
                raise HTTPException(status_code=400, detail=f"Unknown command: {command}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chats")
async def get_chats():
    """List all saved chats."""
    chats = list_chat_records()
    return {"chats": chats}


@app.post("/chats/new")
async def new_chat(request: NewChatRequest | None = None):
    """Create a new chat."""
    global _current_chat_id, _session_usage

    chat_id = request.chat_id if request else None
    chat_id = chat_id or TerminalDemoLauncher.generate_chat_id()

    _current_chat_id = chat_id
    _session_usage = UsageStats()

    agency = get_agency()
    agency.thread_manager.replace_messages([])

    return {"chat_id": chat_id}


@app.get("/chats/{chat_id}")
async def get_chat(chat_id: str):
    """Get details of a specific chat."""
    metadata = load_chat_metadata(chat_id)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
    return metadata


@app.post("/chats/{chat_id}/resume")
async def resume_chat(chat_id: str):
    """Resume a specific chat."""
    global _current_chat_id, _session_usage

    agency = get_agency()

    if load_chat(agency, chat_id):
        _current_chat_id = chat_id
        metadata = load_chat_metadata(chat_id)
        if metadata and "usage" in metadata:
            saved_usage = metadata["usage"]
            _session_usage = UsageStats(**saved_usage)
        else:
            _session_usage = UsageStats()

        return {
            "chat_id": chat_id,
            "messages": agency.thread_manager.get_all_messages(),
            "usage": _session_usage.__dict__ if _session_usage else None,
        }

    raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")


@app.delete("/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a specific chat."""
    chat_file = Path(TerminalDemoLauncher._index_file_path()).parent / f"messages_{chat_id}.json"

    if chat_file.exists():
        chat_file.unlink()
        return {"success": True, "message": f"Deleted chat {chat_id}"}

    raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")


# ============================================================================
# Settings API Routes
# ============================================================================

def _reload_agency_with_settings(settings: dict) -> None:
    """
    Reload the agency with new settings.

    Updates environment variables and recreates the agency instance.
    """
    global _agency

    # Update environment variables with API keys
    api_keys = settings.get("api_keys", {})
    for provider, key_data in api_keys.items():
        if isinstance(key_data, dict) and "key" in key_data:
            key = key_data["key"]
            provider_upper = provider.upper()

            if provider_upper == "OPENAI":
                os.environ["OPENAI_API_KEY"] = key
            elif provider_upper == "ANTHROPIC":
                os.environ["ANTHROPIC_API_KEY"] = key
            elif provider_upper == "GOOGLE":
                os.environ["GOOGLE_API_KEY"] = key
            elif provider_upper == "COHERE":
                os.environ["COHERE_API_KEY"] = key

    # Recreate agency with new settings
    _agency = None  # Reset to force reload on next get_agency() call


@app.get("/settings")
async def get_settings(request: Request):
    """
    Get current settings.

    If settings are encrypted, password must be provided via X-Password header.
    """
    password = request.headers.get("X-Password")

    try:
        manager = get_settings_manager()
        settings = manager.load_settings(password)
        return settings
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/settings")
async def update_settings(request: Request):
    """
    Update settings and reload the agency.

    If settings are encrypted, password must be provided via X-Password header.
    """
    password = request.headers.get("X-Password")

    try:
        settings_data = await request.json()

        manager = get_settings_manager()
        manager.load_settings(password)  # Load first to get current state
        manager.save_settings(settings_data, password)

        # Reload agency with new settings
        _reload_agency_with_settings(settings_data)

        return {
            "success": True,
            "message": "Settings saved and agency reloaded successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/settings/unlock")
async def unlock_settings(request: UnlockSettingsRequest):
    """
    Unlock encrypted settings with password.

    Returns the decrypted settings if password is correct.
    """
    try:
        manager = get_settings_manager()
        settings = manager.load_settings(request.password)

        return {
            "success": True,
            "data": settings,
            "is_encrypted": manager.is_encrypted()
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "is_encrypted": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/settings/validate")
async def validate_api_key(request: ValidateKeyRequest):
    """
    Validate an API key by making a test request to the provider.

    Returns validation result and available models if successful.
    """
    provider = request.provider.lower()
    key = request.key

    try:
        if provider == "openai":
            return await _validate_openai_key(key)
        elif provider == "anthropic":
            return await _validate_anthropic_key(key)
        elif provider == "google":
            return await _validate_google_key(key)
        elif provider == "cohere":
            return await _validate_cohere_key(key)
        else:
            return ValidateKeyResponse(
                valid=False,
                provider=request.provider,
                message=f"Unsupported provider: {provider}",
                error=f"Provider '{provider}' is not supported"
            )
    except Exception as e:
        return ValidateKeyResponse(
            valid=False,
            provider=request.provider,
            message="Validation failed",
            error=str(e)
        )


async def _validate_openai_key(key: str) -> ValidateKeyResponse:
    """Validate OpenAI API key and fetch available models."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                models = [
                    m["id"] for m in data.get("data", [])
                    if m["id"].startswith(("gpt-", "o1-", "o3-"))
                ]

                return ValidateKeyResponse(
                    valid=True,
                    provider="openai",
                    message="API key is valid",
                    models=sorted(models)
                )
            else:
                return ValidateKeyResponse(
                    valid=False,
                    provider="openai",
                    message="Invalid API key",
                    error=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return ValidateKeyResponse(
            valid=False,
            provider="openai",
            message="Validation failed",
            error=str(e)
        )


async def _validate_anthropic_key(key: str) -> ValidateKeyResponse:
    """Validate Anthropic API key."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "."}]
                },
                timeout=10.0
            )

            if response.status_code == 200:
                return ValidateKeyResponse(
                    valid=True,
                    provider="anthropic",
                    message="API key is valid",
                    models=["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
                )
            elif response.status_code == 401:
                return ValidateKeyResponse(
                    valid=False,
                    provider="anthropic",
                    message="Invalid API key",
                    error="Unauthorized"
                )
            else:
                return ValidateKeyResponse(
                    valid=False,
                    provider="anthropic",
                    message="Validation failed",
                    error=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return ValidateKeyResponse(
            valid=False,
            provider="anthropic",
            message="Validation failed",
            error=str(e)
        )


async def _validate_google_key(key: str) -> ValidateKeyResponse:
    """Validate Google API key."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
                timeout=10.0
            )

            if response.status_code == 200:
                return ValidateKeyResponse(
                    valid=True,
                    provider="google",
                    message="API key is valid",
                    models=["gemini-pro", "gemini-pro-vision"]
                )
            else:
                return ValidateKeyResponse(
                    valid=False,
                    provider="google",
                    message="Invalid API key",
                    error=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return ValidateKeyResponse(
            valid=False,
            provider="google",
            message="Validation failed",
            error=str(e)
        )


async def _validate_cohere_key(key: str) -> ValidateKeyResponse:
    """Validate Cohere API key."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.cohere.ai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=10.0
            )

            if response.status_code == 200:
                return ValidateKeyResponse(
                    valid=True,
                    provider="cohere",
                    message="API key is valid",
                    models=["command", "command-light", "embed-english-v2.0"]
                )
            else:
                return ValidateKeyResponse(
                    valid=False,
                    provider="cohere",
                    message="Invalid API key",
                    error=f"HTTP {response.status_code}"
                )
    except Exception as e:
        return ValidateKeyResponse(
            valid=False,
            provider="cohere",
            message="Validation failed",
            error=str(e)
        )


# ============================================================================
# Concurrency API Routes
# ============================================================================

@app.get("/concurrency/locks")
async def get_active_locks():
    """Get all currently active locks."""
    manager = get_global_concurrency_manager()
    return {"locks": manager.get_active_locks()}


@app.get("/concurrency/locks/{lock_id}")
async def get_lock_details(lock_id: str):
    """Get details of a specific lock."""
    manager = get_global_concurrency_manager()
    details = manager.get_lock_details(lock_id)
    if not details:
        raise HTTPException(status_code=404, detail=f"Lock {lock_id} not found")
    return details


@app.post("/concurrency/locks/{lock_id}/override")
async def override_lock(lock_id: str, request: OverrideLockRequest):
    """Manually override/release a lock."""
    manager = get_global_concurrency_manager()
    success = await manager.override_lock(lock_id, request.reason)
    if not success:
        raise HTTPException(status_code=404, detail=f"Lock {lock_id} not found")
    return {"success": True, "message": f"Lock {lock_id} overridden"}


@app.get("/concurrency/history")
async def get_lock_history(limit: int = 100):
    """Get lock event history."""
    manager = get_global_concurrency_manager()
    return {"history": manager.get_lock_history(limit)}


@app.get("/concurrency/conflicts")
async def get_conflicts(limit: int = 50):
    """Get conflict history."""
    manager = get_global_concurrency_manager()
    return {"conflicts": manager.get_conflicts(limit)}


@app.get("/concurrency/analytics")
async def get_analytics(time_range: str = "1h"):
    """Get concurrency analytics."""
    manager = get_global_concurrency_manager()
    return manager.get_analytics(time_range)


@app.get("/concurrency/patterns")
async def get_conflict_patterns(top_n: int = 10):
    """Get conflict hotspots/patterns."""
    manager = get_global_concurrency_manager()
    return {"patterns": manager.get_conflict_patterns(top_n)}


@app.post("/concurrency/deadlocks/detect")
async def detect_deadlocks():
    """Run deadlock detection."""
    manager = get_global_concurrency_manager()
    deadlocks = await manager.detect_deadlocks()
    return {"deadlocks": [d.to_dict() for d in deadlocks]}


@app.post("/concurrency/deadlocks/resolve")
async def resolve_deadlock(request: ResolveDeadlockRequest):
    """Resolve a detected deadlock."""
    manager = get_global_concurrency_manager()

    # Map strategy string to enum
    strategy_map = {
        "priority": DeadlockResolutionStrategy.PRIORITY_BASED,
        "youngest": DeadlockResolutionStrategy.YOUNGEST_FIRST,
        "oldest": DeadlockResolutionStrategy.OLDEST_FIRST,
        "random": DeadlockResolutionStrategy.RANDOM_VICTIM,
        "manual": DeadlockResolutionStrategy.MANUAL_INTERVENTION,
    }

    strategy = strategy_map.get(request.strategy, DeadlockResolutionStrategy.PRIORITY_BASED)

    success = await manager.resolve_deadlock(
        cycle=request.cycle,
        strategy=strategy,
        victim_lock_id=request.victim_lock_id,
    )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to resolve deadlock")

    return {"success": True, "message": "Deadlock resolved"}


@app.websocket("/ws/concurrency")
async def concurrency_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time concurrency events.

    Connect to receive live updates on:
    - Lock acquisition/release
    - Deadlock detection
    - Conflict resolution
    """
    await ws_manager.connect(websocket)

    # Setup event callback on first connection
    setup_concurrency_websocket()

    try:
        # Send initial state
        manager = get_global_concurrency_manager()
        await websocket.send_json({
            "type": "connected",
            "data": {
                "active_locks": manager.get_active_locks(),
            }
        })

        # Keep connection alive and handle any messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle client messages if needed
            await websocket.send_json({"type": "echo", "data": data})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        ws_manager.disconnect(websocket)
        raise


# ============================================================================
# Helper Functions
# ============================================================================

def convert_event_to_sse(event: Any, recipient_agent: str | None) -> dict | None:
    """Convert an OpenAI Agents SDK event to SSE format."""
    try:
        event_type = getattr(event, "type", "")

        # Raw response events (streaming content)
        if event_type == "raw_response_event":
            data = getattr(event, "data", None)
            if not data:
                return None

            data_type = getattr(data, "type", "")

            # Reasoning delta
            if data_type == "response.reasoning_summary_text.delta":
                delta = getattr(data, "delta", "")
                if delta:
                    agent = getattr(event, "agent", recipient_agent or "Assistant")
                    return {
                        "type": "reasoning",
                        "agent": agent,
                        "delta": delta,
                    }

            # Text delta
            elif data_type == "response.output_text.delta":
                delta = getattr(data, "delta", "")
                if delta:
                    agent = getattr(event, "agent", recipient_agent or "Assistant")
                    return {
                        "type": "text",
                        "agent": agent,
                        "delta": delta,
                        "recipient": "user",
                    }

        # Run item events (function calls, etc)
        elif event_type == "run_item_stream_event":
            item = getattr(event, "item", None)
            if not item:
                return None

            item_type = getattr(item, "type", "")

            # Tool call output
            if item_type == "tool_call_output_item":
                output = getattr(item, "output", "")
                return {
                    "type": "function_output",
                    "output": str(output),
                }

    except Exception:
        # Return None on any error to avoid breaking the stream
        return None

    return None


# ============================================================================
# Main
# ============================================================================

def main():
    """Run the server."""
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
