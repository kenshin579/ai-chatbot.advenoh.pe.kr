"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage, Source } from "@/lib/api";
import { sendFeedback } from "@/lib/api";
import { useEffect, useRef, useState } from "react";

interface DisplayMessage extends ChatMessage {
  sources?: Source[];
  message_id?: string;
  question?: string;
}

interface MessageListProps {
  messages: DisplayMessage[];
  isLoading?: boolean;
  blogId: string;
}

type FeedbackState = "idle" | "sending" | "done";

export function MessageList({ messages, isLoading, blogId }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [feedbackMap, setFeedbackMap] = useState<
    Record<string, { state: FeedbackState; rating?: "up" | "down" }>
  >({});

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const handleFeedback = async (
    messageId: string,
    question: string,
    rating: "up" | "down"
  ) => {
    setFeedbackMap((prev) => ({
      ...prev,
      [messageId]: { state: "sending", rating },
    }));
    try {
      await sendFeedback({ message_id: messageId, blog_id: blogId, question, rating });
      setFeedbackMap((prev) => ({
        ...prev,
        [messageId]: { state: "done", rating },
      }));
    } catch {
      setFeedbackMap((prev) => ({
        ...prev,
        [messageId]: { state: "idle" },
      }));
    }
  };

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center text-muted-foreground">
        <p>블로그에 대해 질문해 보세요!</p>
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1 p-4">
      <div className="space-y-4 max-w-3xl mx-auto">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === "human" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                msg.role === "human"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-border/50">
                  <p className="text-xs font-medium mb-1">참고 글:</p>
                  <ul className="space-y-0.5">
                    {msg.sources.map((source, j) => (
                      <li key={j}>
                        <a
                          href={source.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-blue-500 hover:underline"
                        >
                          {source.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {msg.role === "ai" && msg.message_id && msg.question && (() => {
                const fb = feedbackMap[msg.message_id] ?? { state: "idle" };
                const isSending = fb.state === "sending";
                const isDone = fb.state === "done";
                return (
                  <div className="mt-2 pt-2 border-t border-border/50 flex items-center gap-2">
                    {isDone ? (
                      <span className="text-xs text-muted-foreground">
                        피드백 감사합니다 {fb.rating === "up" ? "👍" : "👎"}
                      </span>
                    ) : (
                      <>
                        <span className="text-xs text-muted-foreground">도움이 됐나요?</span>
                        <button
                          onClick={() => handleFeedback(msg.message_id!, msg.question!, "up")}
                          disabled={isSending}
                          className="text-sm disabled:opacity-40 hover:scale-110 transition-transform"
                          aria-label="좋아요"
                        >
                          👍
                        </button>
                        <button
                          onClick={() => handleFeedback(msg.message_id!, msg.question!, "down")}
                          disabled={isSending}
                          className="text-sm disabled:opacity-40 hover:scale-110 transition-transform"
                          aria-label="별로예요"
                        >
                          👎
                        </button>
                        {isSending && (
                          <span className="text-xs text-muted-foreground animate-pulse">전송 중...</span>
                        )}
                      </>
                    )}
                  </div>
                );
              })()}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-2">
              <p className="text-sm text-muted-foreground animate-pulse">
                답변을 생성하고 있습니다...
              </p>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
