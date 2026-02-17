"use client";

import { ChatInput } from "@/components/ChatInput";
import { MessageList } from "@/components/MessageList";
import type { ChatMessage, Source } from "@/lib/api";
import { sendChat } from "@/lib/api";
import { useBlog } from "@/lib/BlogContext";
import { useCallback, useState } from "react";

interface DisplayMessage extends ChatMessage {
  sources?: Source[];
  message_id?: string;
  question?: string;
}

export function ChatWindow() {
  const { blogId } = useBlog();
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
          message_id: response.message_id,
          question,
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
      {/* Messages */}
      <MessageList messages={messages} isLoading={isLoading} blogId={blogId} />

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
