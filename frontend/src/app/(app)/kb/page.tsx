"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import Link from "next/link";
import { useDebounce } from "use-debounce";
import { format } from "date-fns";

export default function KnowledgeBasePage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [debouncedSearch] = useDebounce(searchTerm, 500);

  const { data: articles, isLoading } = useQuery({
    queryKey: ["kb_articles", debouncedSearch],
    queryFn: async () => {
      const params = new URLSearchParams({ page_size: "50" });
      if (debouncedSearch) params.append("q", debouncedSearch);

      const res = await fetchWithAuth(`/kb/articles?${params.toString()}`);
      if (!res.ok) throw new Error("Failed to load articles");
      return res.json();
    }
  });

  const { data: categories } = useQuery({
    queryKey: ["kb_categories"],
    queryFn: async () => {
      const res = await fetchWithAuth("/kb/categories");
      if (!res.ok) throw new Error("Failed to load categories");
      return res.json();
    }
  });

  return (
    <div className="max-w-5xl mx-auto space-y-8 h-full">
      <div className="text-center space-y-4 py-8">
        <h1 className="text-4xl font-bold text-white">How can we help?</h1>
        <p className="text-slate-400 text-lg">Search the knowledge base for guides, SOPs, and troubleshooting steps.</p>
        <div className="max-w-2xl mx-auto relative mt-6">
          <input
            type="text"
            placeholder="Search articles..."
            className="w-full bg-slate-900 border-2 border-indigo-500/50 text-white rounded-full px-6 py-4 text-lg focus:outline-none focus:border-indigo-500 shadow-lg shadow-indigo-500/10"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {!debouncedSearch && categories && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {categories.map((cat: any) => (
            <div key={cat.id} className="bg-slate-800 p-6 rounded-xl border border-slate-700 hover:border-indigo-500 transition-colors cursor-pointer text-center">
              <h3 className="font-bold text-white mb-2">{cat.name}</h3>
              <p className="text-xs text-slate-400">{cat.description}</p>
            </div>
          ))}
        </div>
      )}

      <div>
        <h2 className="text-xl font-bold text-white mb-4">
          {debouncedSearch ? "Search Results" : "Latest Articles"}
        </h2>
        {isLoading ? (
          <div className="text-slate-400">Loading articles...</div>
        ) : articles?.length === 0 ? (
          <div className="text-slate-400">No articles found matching your query.</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {articles?.map((article: any) => (
              <Link href={`/kb/${article.id}`} key={article.id}>
                <div className="bg-slate-800 p-6 rounded-lg border border-slate-700 hover:bg-slate-750 hover:border-indigo-400 transition-colors h-full flex flex-col">
                  <h3 className="text-lg font-bold text-indigo-400 mb-2">{article.title}</h3>
                  <p className="text-slate-400 text-sm line-clamp-2 mb-4 flex-1">
                    {article.body.replace(/[#*`>]/g, '').substring(0, 150)}...
                  </p>
                  <div className="flex justify-between items-center text-xs text-slate-500 mt-auto pt-4 border-t border-slate-700">
                    <div className="flex gap-2">
                      {article.tags?.slice(0,2).map((tag: string) => (
                        <span key={tag} className="bg-slate-900 px-2 py-1 rounded text-slate-400">#{tag}</span>
                      ))}
                    </div>
                    <span>{article.view_count} views • {format(new Date(article.updated_at), "MMM d")}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
