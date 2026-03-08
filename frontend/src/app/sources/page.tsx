"use client";

import { useEffect, useState } from "react";
import ManualInjectPanel from "@/components/sources/ManualInjectPanel";
import PollStatusPanel from "@/components/sources/PollStatusPanel";

interface Source {
  id: number;
  name: string;
  feed_url: string | null;
  source_type: string | null;
  layer: number | null;
  bias_label: string | null;
  language: string | null;
  is_active: boolean | null;
  article_count: number;
  economic_school: string | null;
  economic_bias: string | null;
  analytical_framework: string | null;
  salience_domains: string | null;
}

interface PollStatus {
  last_poll_started: string | null;
  last_poll_completed: string | null;
  last_poll_duration_seconds: number | null;
  is_polling: boolean;
  total_polls: number;
  next_scheduled_poll: string | null;
  results: { source_name: string; new_articles: number; polled_at: string }[];
}

const BIAS_COLORS: Record<string, string> = {
  center: "text-gray-300 bg-gray-800",
  left: "text-blue-300 bg-blue-900",
  right: "text-red-300 bg-red-900",
  "center-left": "text-blue-200 bg-blue-950",
  "center-right": "text-red-200 bg-red-950",
  "state-affiliated": "text-orange-300 bg-orange-900",
  independent: "text-green-300 bg-green-900",
  unknown: "text-gray-400 bg-gray-800",
};

const ECON_BIAS_COLORS: Record<string, string> = {
  progressive: "text-teal-300 bg-teal-900",
  center: "text-gray-300 bg-gray-800",
  "market-oriented": "text-yellow-300 bg-yellow-900",
  "state-directed": "text-orange-300 bg-orange-900",
};

const IR_FRAMEWORK_COLORS: Record<string, string> = {
  realist: "text-red-300 bg-red-950",
  liberal: "text-blue-300 bg-blue-950",
  constructivist: "text-purple-300 bg-purple-950",
  critical: "text-pink-300 bg-pink-950",
  empirical: "text-gray-300 bg-gray-800",
  mixed: "text-indigo-300 bg-indigo-950",
};

export default function SourcesPage() {
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(true);
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<string>("");
  const [pollStatus, setPollStatus] = useState<PollStatus | null>(null);

  const fetchSources = () => {
    fetch("http://localhost:8000/api/sources")
      .then((r) => r.json())
      .then(setSources)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const fetchPollStatus = () => {
    fetch("http://localhost:8000/api/sources/poll-status")
      .then((r) => r.json())
      .then(setPollStatus)
      .catch(console.error);
  };

  useEffect(() => {
    fetchSources();
    fetchPollStatus();
    const interval = setInterval(fetchPollStatus, 30_000);
    return () => clearInterval(interval);
  }, []);

  const handleIngest = async () => {
    setIngesting(true);
    setIngestResult("");
    try {
      const res = await fetch("http://localhost:8000/api/sources/ingest", { method: "POST" });
      const data = await res.json();
      setIngestResult(`Ingested ${data.total_new} new articles across ${Object.keys(data.by_source).length} sources`);
      fetchSources();
      fetchPollStatus();
    } catch (err) {
      setIngestResult(`Error: ${err}`);
    } finally {
      setIngesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Sources</h1>
        <button
          onClick={handleIngest}
          disabled={ingesting}
          className="px-4 py-2 bg-green-700 hover:bg-green-600 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
        >
          {ingesting ? "Polling..." : "Poll RSS Now"}
        </button>
      </div>

      <PollStatusPanel status={pollStatus} />

      {ingestResult && (
        <div className="p-3 bg-gray-900 rounded-lg border border-gray-800 text-sm text-gray-300">
          {ingestResult}
        </div>
      )}

      <ManualInjectPanel onInjected={fetchSources} />

      {loading ? (
        <div className="text-gray-400">Loading sources...</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400 border-b border-gray-800">
                <th className="pb-2 pr-4">Source</th>
                <th className="pb-2 pr-4">Layer</th>
                <th className="pb-2 pr-4">Social Bias</th>
                <th className="pb-2 pr-4">Econ Bias</th>
                <th className="pb-2 pr-4">IR Framework</th>
                <th className="pb-2 pr-4">Econ School</th>
                <th className="pb-2 pr-4">Lang</th>
                <th className="pb-2 pr-4">Articles</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-900">
              {sources.map((s) => (
                <tr key={s.id} className="text-gray-300 hover:bg-gray-900 transition-colors">
                  <td className="py-2 pr-4">
                    <p className="font-medium text-white">{s.name}</p>
                    {s.feed_url && (
                      <p className="text-xs text-gray-500 truncate max-w-[200px]">{s.feed_url}</p>
                    )}
                    {s.salience_domains && (
                      <p className="text-xs text-gray-600 mt-0.5">{s.salience_domains}</p>
                    )}
                  </td>
                  <td className="py-2 pr-4">{s.layer ?? "—"}</td>
                  <td className="py-2 pr-4">
                    <span className={`px-2 py-0.5 rounded text-xs ${BIAS_COLORS[s.bias_label || "unknown"] ?? BIAS_COLORS.unknown}`}>
                      {s.bias_label || "unknown"}
                    </span>
                  </td>
                  <td className="py-2 pr-4">
                    {s.economic_bias ? (
                      <span className={`px-2 py-0.5 rounded text-xs ${ECON_BIAS_COLORS[s.economic_bias] ?? "text-gray-400 bg-gray-800"}`}>
                        {s.economic_bias}
                      </span>
                    ) : <span className="text-gray-600">—</span>}
                  </td>
                  <td className="py-2 pr-4">
                    {s.analytical_framework ? (
                      <span className={`px-2 py-0.5 rounded text-xs ${IR_FRAMEWORK_COLORS[s.analytical_framework] ?? "text-gray-400 bg-gray-800"}`}>
                        {s.analytical_framework}
                      </span>
                    ) : <span className="text-gray-600">—</span>}
                  </td>
                  <td className="py-2 pr-4">
                    <span className="text-xs text-gray-400">{s.economic_school ?? "—"}</span>
                  </td>
                  <td className="py-2 pr-4">{s.language ?? "—"}</td>
                  <td className="py-2 pr-4">{s.article_count}</td>
                  <td className="py-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${s.is_active ? "bg-green-900 text-green-300" : "bg-gray-800 text-gray-500"}`}>
                      {s.is_active ? "active" : "inactive"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
