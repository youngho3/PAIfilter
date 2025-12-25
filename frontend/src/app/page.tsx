"use client";

import { useState } from "react";
import axios from "axios";
import { BrainCircuit, Send, Sparkles, Activity } from "lucide-react";

export default function Home() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!input.trim()) return;
    
    setLoading(true);
    setError("");
    setResult(null);

    try {
      // 1. Vectorize API 호출
      const vecResponse = await axios.post("http://localhost:8000/api/v1/vectorize", {
        text: input,
      });

      // 2. Context Save API 호출 (Pinecone 저장)
      try {
        await axios.post("http://localhost:8000/api/v1/context", {
          text: input,
        });
        console.log("Context saved to Pinecone");
      } catch (saveErr) {
        console.warn("Failed to save context:", saveErr);
      }

      // 3. Insight API 호출
      const insightResponse = await axios.post("http://localhost:8000/api/v1/insight", {
        text: input,
      });

            setResult({

              vector: vecResponse.data,

              insight: insightResponse.data.insight,

              context_used: insightResponse.data.context_used,

              saved: true

            });

          } catch (err) {

            console.error(err);

            setError("AI 서버 연결에 실패했습니다. 백엔드가 실행 중인지 확인해주세요.");

          } finally {

            setLoading(false);

          }

        };

      

        return (

          <main className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">

            <div className="max-w-4xl mx-auto space-y-12">

              {/* ... Header & Input Sections (No Change) ... */}

              

              {/* Header */}

              <header className="flex items-center space-x-3 border-b border-slate-800 pb-6">

                <div className="p-3 bg-indigo-600 rounded-lg">

                  <BrainCircuit size={32} className="text-white" />

                </div>

                <div>

                  <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-cyan-400">

                    PAI

                  </h1>

                  <p className="text-slate-400">Personal AI Filter</p>

                </div>

              </header>

      

              {/* Input Section */}

              <section className="space-y-4">

                <div className="flex items-center space-x-2 text-indigo-400 font-semibold">

                  <Activity size={20} />

                  <h2>Context Injection</h2>

                </div>

                <p className="text-slate-400 text-sm">

                  현재 당신의 가장 큰 비즈니스 고민이나 관심사를 입력하세요. AI가 이를 벡터화하여 기억합니다.

                </p>

                

                <div className="relative">

                  <textarea

                    value={input}

                    onChange={(e) => setInput(e.target.value)}

                    placeholder="예: SaaS 제품의 초기 유저를 어떻게 1,000명까지 늘릴 수 있을지 고민이야. 마케팅 예산은 부족하고..."

                    className="w-full h-40 bg-slate-900 border border-slate-700 rounded-xl p-6 text-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all resize-none shadow-inner"

                  />

                  <button

                    onClick={handleAnalyze}

                    disabled={loading || !input}

                    className={`absolute bottom-4 right-4 flex items-center space-x-2 px-6 py-2 rounded-lg font-semibold transition-all ${

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

                        <span>Analyze PAI</span>

                      </>

                    )}

                  </button>

                </div>

              </section>

      

              {/* Result Section */}

              {error && (

                <div className="p-4 bg-red-900/50 border border-red-700 text-red-200 rounded-lg">

                  ⚠️ {error}

                </div>

              )}

      

              {result && (

                <section className="space-y-6 animate-fade-in-up">

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                    

                    {/* Insight Card */}

                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 space-y-4 hover:border-indigo-500/50 transition-colors">

                      <div className="flex items-center space-x-2 text-cyan-400 font-semibold">

                        <Sparkles size={20} />

                        <h3>AI Insight (Reasoning)</h3>

                      </div>

                      <div className="prose prose-invert prose-sm max-w-none text-slate-300 whitespace-pre-wrap">

                        {result.insight}

                      </div>

                      

                      {/* Referenced Memory */}

                      {result.context_used && result.context_used.length > 0 && (

                        <div className="mt-4 pt-4 border-t border-slate-800">

                          <p className="text-xs text-indigo-400 mb-2 font-semibold">Referenced Memory (RAG)</p>

                          <ul className="space-y-1">

                            {result.context_used.map((ctx: string, idx: number) => (

                              <li key={idx} className="text-xs text-slate-500 bg-slate-950 p-2 rounded truncate">

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

                          <h3>Vector Data (Memory)</h3>

                        </div>

                        {result.saved && (

                          <span className="px-2 py-1 text-xs font-bold text-emerald-950 bg-emerald-400 rounded-full animate-pulse">

                            SAVED

                          </span>

                        )}

                      </div>

                      <div className="space-y-2 text-sm">

                        <div className="flex justify-between text-slate-400">

                          <span>Dimension</span>

                          <span className="font-mono text-white">{result.vector.vector_dimension}d</span>

                        </div>

                        <div className="flex justify-between text-slate-400">

                          <span>Model</span>

                          <span className="font-mono text-white">text-embedding-004</span>

                        </div>

                        <div className="mt-4 pt-4 border-t border-slate-800">

                          <p className="text-xs text-slate-500 mb-2">Vector Preview (Float32)</p>

                          <div className="font-mono text-xs text-emerald-500/80 break-all bg-slate-950 p-3 rounded">

                            [{result.vector.vector_preview.map((v: number) => v.toFixed(6)).join(", ")}...]

                          </div>

                        </div>

                      </div>

                    </div>

      

                  </div>

                </section>

              )}

            </div>

          </main>

        );

      }

      