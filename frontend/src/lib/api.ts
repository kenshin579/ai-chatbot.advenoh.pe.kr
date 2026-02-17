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
  message_id: string;
}

export interface FeedbackRequest {
  message_id: string;
  blog_id: string;
  question: string;
  rating: "up" | "down";
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

export async function sendFeedback(request: FeedbackRequest): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
}

export interface AdminStats {
  daily_queries: { date: string; count: number }[];
  top_questions: { question: string; count: number }[];
  feedback_score: { total: number; up: number; down: number; up_ratio: number };
  avg_response_time: number;
  search_failure_rate: number;
}

export async function getAdminStats(): Promise<AdminStats> {
  const res = await fetch(`${API_BASE_URL}/admin/stats`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
