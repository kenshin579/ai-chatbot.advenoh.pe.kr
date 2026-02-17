"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

interface BlogContextType {
  blogId: string;
  setBlogId: (id: string) => void;
}

const BlogContext = createContext<BlogContextType | null>(null);

export function BlogProvider({ children }: { children: ReactNode }) {
  const [blogId, setBlogId] = useState("blog-v2");
  return (
    <BlogContext.Provider value={{ blogId, setBlogId }}>
      {children}
    </BlogContext.Provider>
  );
}

export function useBlog() {
  const ctx = useContext(BlogContext);
  if (!ctx) throw new Error("useBlog must be used within BlogProvider");
  return ctx;
}
