export interface ChatMessage {
  role: "human" | "ai";
  content: string;
}

export interface Source {
  title: string;
  url: string;
}

export interface ChatRequest {
  blog_id: string;
  question: string;
  chat_history?: ChatMessage[];
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";

export async function sendChat(request: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}
