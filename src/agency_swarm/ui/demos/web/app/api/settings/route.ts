import { NextRequest, NextResponse } from "next/server";

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || "http://localhost:8000";

export async function GET(request: NextRequest) {
  try {
    const password = request.headers.get("X-Password") || undefined;

    const response = await fetch(`${PYTHON_BACKEND_URL}/settings`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        ...(password ? { "X-Password": password } : {}),
      },
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: response.statusText },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Settings GET error:", error);
    return NextResponse.json(
      { error: "Failed to fetch settings" },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const password = request.headers.get("X-Password") || undefined;
    const body = await request.json();

    const response = await fetch(`${PYTHON_BACKEND_URL}/settings`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...(password ? { "X-Password": password } : {}),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      return NextResponse.json(
        { error: response.statusText },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Settings PUT error:", error);
    return NextResponse.json(
      { error: "Failed to update settings" },
      { status: 500 }
    );
  }
}
