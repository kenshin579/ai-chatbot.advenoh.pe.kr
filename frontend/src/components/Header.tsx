"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ExternalLink, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

const EXTERNAL_LINKS = [
  { label: "IT Blog", url: "https://blog-v2.advenoh.pe.kr" },
  { label: "Investment Blog", url: "https://investment.advenoh.pe.kr" },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="flex h-14 items-center justify-between border-b px-4">
      <Link href="/" className="text-lg font-semibold hover:opacity-80">
        Blog Q&A Chatbot
      </Link>

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
