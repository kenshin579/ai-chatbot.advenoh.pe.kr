"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import type { ChatMessage, Source } from "@/lib/api";
import { useEffect, useRef } from "react";

interface DisplayMessage extends ChatMessage {
  sources?: Source[];
}

interface MessageListProps {
  messages: DisplayMessage[];
  isLoading?: boolean;
}

export function MessageList({ messages, isLoading }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

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
