"use client";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Send } from "lucide-react";
import { FormEvent, useState } from "react";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setInput("");
  };

  return (
    <form onSubmit={handleSubmit} className="p-4">
      <div className="relative mx-auto max-w-2xl">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="블로그에 질문하기"
          disabled={disabled}
          className="rounded-full py-3 pl-4 pr-12 shadow-sm"
        />
        <Button
          type="submit"
          size="icon"
          disabled={disabled || !input.trim()}
          className="absolute right-1.5 top-1/2 -translate-y-1/2 h-8 w-8 rounded-full"
          aria-label="전송"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </form>
  );
}
