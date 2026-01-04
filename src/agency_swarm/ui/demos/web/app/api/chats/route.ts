import { NextRequest, NextResponse } from "next/server";

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

// GET /api/chats - List all chats
export async function GET() {
  try {
    const response = await fetch(`${PYTHON_BACKEND_URL}/chats`, {
      method: "GET",
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `Backend error: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}

// POST /api/chats/new - Create new chat
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { chat_id } = body;

    const response = await fetch(`${PYTHON_BACKEND_URL}/chats/new`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: chat_id ? JSON.stringify({ chat_id }) : undefined,
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: `Backend error: ${response.status}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    );
  }
}
