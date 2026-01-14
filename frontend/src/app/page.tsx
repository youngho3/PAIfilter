"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import {
  BrainCircuit,
  Sparkles,
  Activity,
  Newspaper,
  RefreshCw,
  ExternalLink,
  TrendingUp,
  Zap,
} from "lucide-react";

interface Signal {
  article: {
    id: string;
    title: string;
    url: string;
    source: string;
    summary: string;
    published_at: string | null;
  };
  score: number;
  similarity: number;
}

interface SignalStats {
  news_articles_count: number;
  feeds_configured: number;
  status: string;
}

export default function Home() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Signal Dashboard State
  const [signals, setSignals] = useState<Signal[]>([]);
  const [signalLoading, setSignalLoading] = useState(false);
  const [fetchingNews, setFetchingNews] = useState(false);
  const [stats, setStats] = useState<SignalStats | null>(null);
  const [activeTab, setActiveTab] = useState<"context" | "signals">("context");

  // Fetch stats on load
  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get("http://localhost:8000/api/v1/signals/stats");
      setStats(response.data);
    } catch (err) {
      console.warn("Failed to fetch stats:", err);
    }
  };

  const handleAnalyze = async () => {
    if (!input.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const vecResponse = await axios.post("http://localhost:8000/api/v1/vectorize", {
        text: input,
      });

      try {
        await axios.post("http://localhost:8000/api/v1/context", {
          text: input,
        });
      } catch (saveErr) {
        console.warn("Failed to save context:", saveErr);
      }

      const insightResponse = await axios.post("http://localhost:8000/api/v1/insight", {
        text: input,
      });

      setResult({
        vector: vecResponse.data,
        insight: insightResponse.data.insight,
        context_used: insightResponse.data.context_used,
        saved: true,
      });
    } catch (err) {
      console.error(err);
      setError("AI 서버 연결에 실패했습니다. 백엔드가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  const handleFetchNews = async () => {
    setFetchingNews(true);
    setError("");

    try {
      const response = await axios.post("http://localhost:8000/api/v1/feeds/fetch?limit_per_feed=5");
      await fetchStats();
      alert(`${response.data.message}`);
    } catch (err) {
      console.error(err);
      setError("뉴스 수집에 실패했습니다.");
    } finally {
      setFetchingNews(false);
    }
  };

  const handleGetSignals = async () => {
    if (!input.trim()) {
      setError("관심사를 먼저 입력해주세요.");
      return;
    }

    setSignalLoading(true);
    setError("");

    try {
      const response = await axios.post(
        "http://localhost:8000/api/v1/signals?top_k=10&min_score=2",
        { text: input }
      );
      setSignals(response.data.signals);
    } catch (err) {
      console.error(err);
      setError("시그널 생성에 실패했습니다.");
    } finally {
      setSignalLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return "text-emerald-400 bg-emerald-400/10";
    if (score >= 6) return "text-cyan-400 bg-cyan-400/10";
    if (score >= 4) return "text-yellow-400 bg-yellow-400/10";
    return "text-slate-400 bg-slate-400/10";
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("ko-KR", { month: "short", day: "numeric" });
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-slate-800 pb-6">
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-indigo-600 rounded-lg">
              <BrainCircuit size={32} className="text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">
                PAI
              </h1>
              <p className="text-slate-400">Personal AI Filter</p>
            </div>
          </div>

          {/* Stats Badge */}
          {stats && (
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2 text-slate-400">
                <Newspaper size={16} />
                <span>{stats.news_articles_count} articles</span>
              </div>
              <div
                className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  stats.status === "ready"
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "bg-yellow-500/20 text-yellow-400"
                }`}
              >
                {stats.status === "ready" ? "Ready" : "Empty"}
              </div>
            </div>
          )}
        </header>

        {/* Tabs */}
        <div className="flex space-x-2 border-b border-slate-800">
          <button
            onClick={() => setActiveTab("context")}
            className={`px-4 py-2 font-semibold transition-colors ${
              activeTab === "context"
                ? "text-indigo-400 border-b-2 border-indigo-400"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            <Activity size={16} className="inline mr-2" />
            Context Injection
          </button>
          <button
            onClick={() => setActiveTab("signals")}
            className={`px-4 py-2 font-semibold transition-colors ${
              activeTab === "signals"
                ? "text-cyan-400 border-b-2 border-cyan-400"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            <Zap size={16} className="inline mr-2" />
            Signal Dashboard
          </button>
        </div>

        {/* Input Section (Common) */}
        <section className="space-y-4">
          <p className="text-slate-400 text-sm">
            {activeTab === "context"
              ? "현재 당신의 가장 큰 비즈니스 고민이나 관심사를 입력하세요. AI가 이를 벡터화하여 기억합니다."
              : "관심사를 입력하고 매칭되는 뉴스 시그널을 확인하세요."}
          </p>

          <div className="relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="예: SaaS 제품의 초기 유저를 어떻게 1,000명까지 늘릴 수 있을지 고민이야. 마케팅 예산은 부족하고..."
              className="w-full h-32 bg-slate-900 border border-slate-700 rounded-xl p-6 text-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all resize-none shadow-inner"
            />

            <div className="absolute bottom-4 right-4 flex items-center space-x-2">
              {activeTab === "context" ? (
                <button
                  onClick={handleAnalyze}
                  disabled={loading || !input}
                  className={`flex items-center space-x-2 px-6 py-2 rounded-lg font-semibold transition-all ${
                    loading || !input
                      ? "bg-slate-700 text-slate-500 cursor-not-allowed"
                      : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg hover:shadow-indigo-500/30"
                  }`}
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Processing...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={18} />
                      <span>Analyze</span>
                    </>
                  )}
                </button>
              ) : (
                <button
                  onClick={handleGetSignals}
                  disabled={signalLoading || !input}
                  className={`flex items-center space-x-2 px-6 py-2 rounded-lg font-semibold transition-all ${
                    signalLoading || !input
                      ? "bg-slate-700 text-slate-500 cursor-not-allowed"
                      : "bg-cyan-600 hover:bg-cyan-500 text-white shadow-lg hover:shadow-cyan-500/30"
                  }`}
                >
                  {signalLoading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>Searching...</span>
                    </>
                  ) : (
                    <>
                      <TrendingUp size={18} />
                      <span>Get Signals</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        </section>

        {/* Error */}
        {error && (
          <div className="p-4 bg-red-900/50 border border-red-700 text-red-200 rounded-lg">
            ⚠️ {error}
          </div>
        )}

        {/* Context Tab Content */}
        {activeTab === "context" && result && (
          <section className="space-y-6 animate-fade-in-up">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Insight Card */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-4 hover:border-indigo-500/50 transition-colors">
                <div className="flex items-center space-x-2 text-cyan-400 font-semibold">
                  <Sparkles size={20} />
                  <h3>AI Insight</h3>
                </div>
                <div className="prose prose-invert prose-sm max-w-none text-slate-300 whitespace-pre-wrap">
                  {result.insight}
                </div>

                {result.context_used && result.context_used.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-800">
                    <p className="text-xs text-indigo-400 mb-2 font-semibold">
                      Referenced Memory (RAG)
                    </p>
                    <ul className="space-y-1">
                      {result.context_used.map((ctx: string, idx: number) => (
                        <li
                          key={idx}
                          className="text-xs text-slate-500 bg-slate-950 p-2 rounded truncate"
                        >
                          {ctx}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Vector Card */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-emerald-400 font-semibold">
                    <Activity size={20} />
                    <h3>Vector Data</h3>
                  </div>
                  {result.saved && (
                    <span className="px-2 py-1 text-xs font-bold text-emerald-950 bg-emerald-400 rounded-full">
                      SAVED
                    </span>
                  )}
                </div>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-slate-400">
                    <span>Dimension</span>
                    <span className="font-mono text-white">
                      {result.vector.vector_dimension}d
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Model</span>
                    <span className="font-mono text-white">text-embedding-004</span>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* Signals Tab Content */}
        {activeTab === "signals" && (
          <section className="space-y-6">
            {/* Fetch News Button */}
            <div className="flex items-center justify-between">
              <p className="text-slate-400 text-sm">
                {signals.length > 0
                  ? `${signals.length}개의 관련 시그널을 찾았습니다.`
                  : "관심사를 입력하고 시그널을 검색하세요."}
              </p>
              <button
                onClick={handleFetchNews}
                disabled={fetchingNews}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                  fetchingNews
                    ? "bg-slate-700 text-slate-500 cursor-not-allowed"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                }`}
              >
                <RefreshCw size={16} className={fetchingNews ? "animate-spin" : ""} />
                <span>{fetchingNews ? "Fetching..." : "Fetch News"}</span>
              </button>
            </div>

            {/* Signal Cards */}
            {signals.length > 0 && (
              <div className="grid grid-cols-1 gap-4">
                {signals.map((signal, idx) => (
                  <div
                    key={signal.article.id || idx}
                    className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:border-cyan-500/50 transition-all group"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs text-slate-500">{signal.article.source}</span>
                          <span className="text-xs text-slate-600">•</span>
                          <span className="text-xs text-slate-500">
                            {formatDate(signal.article.published_at)}
                          </span>
                        </div>
                        <a
                          href={signal.article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-lg font-semibold text-slate-100 hover:text-cyan-400 transition-colors line-clamp-2 flex items-center gap-2"
                        >
                          {signal.article.title}
                          <ExternalLink
                            size={14}
                            className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                          />
                        </a>
                        {signal.article.summary && (
                          <p className="text-sm text-slate-400 mt-2 line-clamp-2">
                            {signal.article.summary}
                          </p>
                        )}
                      </div>

                      {/* Score Badge */}
                      <div
                        className={`flex-shrink-0 px-3 py-2 rounded-lg font-bold text-lg ${getScoreColor(
                          signal.score
                        )}`}
                      >
                        {signal.score.toFixed(1)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {signals.length === 0 && !signalLoading && (
              <div className="text-center py-12 text-slate-500">
                <Newspaper size={48} className="mx-auto mb-4 opacity-50" />
                <p>관심사를 입력하고 &quot;Get Signals&quot; 버튼을 클릭하세요.</p>
                <p className="text-sm mt-2">
                  뉴스가 없다면 먼저 &quot;Fetch News&quot; 버튼으로 뉴스를 수집하세요.
                </p>
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
