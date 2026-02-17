"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ExternalLink, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useBlog } from "@/lib/BlogContext";

const BLOG_OPTIONS = [
  { value: "blog-v2", label: "IT Blog" },
  { value: "investment", label: "Investment Blog" },
];

const EXTERNAL_LINKS = [
  { label: "IT Blog", url: "https://blog-v2.advenoh.pe.kr" },
  { label: "Investment Blog", url: "https://investment.advenoh.pe.kr" },
];

export function Header() {
  const pathname = usePathname();
  const { blogId, setBlogId } = useBlog();
  const isChat = pathname === "/";

  return (
    <header className="flex h-14 items-center justify-between border-b px-4">
      <div className="flex items-center gap-3">
        <Link href="/" className="text-lg font-semibold hover:opacity-80">
          Blog Q&A Chatbot
        </Link>
        {isChat && (
          <Select value={blogId} onValueChange={setBlogId}>
            <SelectTrigger className="w-[160px] h-8 text-sm">
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
        )}
      </div>

      <div className="flex items-center gap-2">
        <Link
          href="/admin"
          className={cn(
            "text-sm hover:underline underline-offset-4",
            pathname === "/admin"
              ? "font-bold text-foreground"
              : "text-muted-foreground"
          )}
        >
          Admin
        </Link>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon-sm">
              <Menu className="size-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>블로그 바로가기</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {EXTERNAL_LINKS.map((link) => (
              <DropdownMenuItem key={link.url} asChild>
                <a
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2"
                >
                  {link.label}
                  <ExternalLink className="size-3 text-muted-foreground" />
                </a>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
