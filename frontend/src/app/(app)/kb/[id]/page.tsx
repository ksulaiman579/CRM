"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchWithAuth } from "@/lib/api";
import Link from "next/link";
import { format } from "date-fns";

export default function ArticleReadingPage({ params }: { params: { id: string } }) {
  const { data: article, isLoading } = useQuery({
    queryKey: ["kb_article", params.id],
    queryFn: async () => {
      const res = await fetchWithAuth(`/kb/articles/${params.id}`);
      if (!res.ok) throw new Error("Failed to load article");
      return res.json();
    }
  });

  if (isLoading) {
    return <div className="max-w-4xl mx-auto py-8 text-slate-400">Loading article...</div>;
  }

  if (!article) {
    return <div className="max-w-4xl mx-auto py-8 text-slate-400">Article not found.</div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8 h-full py-8">
      <Link href="/kb" className="text-indigo-400 hover:underline mb-8 inline-block">
        ← Back to Knowledge Base
      </Link>

      <div className="bg-slate-800 p-10 rounded-xl border border-slate-700">
        <h1 className="text-4xl font-bold text-white mb-6">{article.title}</h1>
        
        <div className="flex items-center gap-6 text-sm text-slate-400 border-b border-slate-700 pb-6 mb-8">
          <div>
            <span className="font-semibold text-slate-300">Last updated:</span> {format(new Date(article.updated_at), "PPP")}
          </div>
          <div>
            <span className="font-semibold text-slate-300">Views:</span> {article.view_count}
          </div>
          <div className="flex gap-2">
            {article.tags?.map((tag: string) => (
              <span key={tag} className="bg-slate-900 px-2 py-0.5 rounded border border-slate-700 text-slate-300">#{tag}</span>
            ))}
          </div>
        </div>

        <div className="prose prose-invert prose-indigo max-w-none">
           {/* In a real app we would use a markdown parser like ReactMarkdown here */}
           <div className="whitespace-pre-wrap text-slate-300 leading-relaxed text-lg">
             {article.body}
           </div>
        </div>
      </div>
    </div>
  );
}
