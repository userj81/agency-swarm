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
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
