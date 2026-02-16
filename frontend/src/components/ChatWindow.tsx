"use client";

import { ChatInput } from "@/components/ChatInput";
import { MessageList } from "@/components/MessageList";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { ChatMessage, Source } from "@/lib/api";
import { sendChat } from "@/lib/api";
import { useCallback, useState } from "react";

interface DisplayMessage extends ChatMessage {
  sources?: Source[];
}

const BLOG_OPTIONS = [
  { value: "blog-v2", label: "IT Blog" },
  { value: "investment", label: "Investment Blog" },
];

export function ChatWindow() {
  const [blogId, setBlogId] = useState("blog-v2");
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = useCallback(
    async (question: string) => {
      setError(null);

      const userMessage: DisplayMessage = { role: "human", content: question };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        // 대화 히스토리 구성 (소스 제외)
        const chatHistory: ChatMessage[] = messages.map((m) => ({
          role: m.role,
          content: m.content,
        }));

        const response = await sendChat({
          blog_id: blogId,
          question,
          chat_history: chatHistory.length > 0 ? chatHistory : undefined,
        });

        const aiMessage: DisplayMessage = {
          role: "ai",
          content: response.answer,
          sources: response.sources,
        };
        setMessages((prev) => [...prev, aiMessage]);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
        setError(message);
      } finally {
        setIsLoading(false);
      }
    },
    [blogId, messages]
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <h1 className="text-lg font-semibold">Blog Q&A Chatbot</h1>
        <Select value={blogId} onValueChange={setBlogId}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {BLOG_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Messages */}
      <MessageList messages={messages} isLoading={isLoading} />

      {/* Error */}
      {error && (
        <div className="px-4 py-2 text-sm text-destructive bg-destructive/10">
          {error}
        </div>
      )}

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={isLoading} />
    </div>
  );
}
