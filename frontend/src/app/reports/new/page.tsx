"use client";

import { useState } from "react";
import StreamingOutput from "@/components/report/StreamingOutput";
import BatchProgress from "@/components/report/BatchProgress";

const DOMAINS = ["general", "geopolitics", "markets", "taiwan", "energy"];

interface IdentifiedTopic {
  topic: string;
  domain: string;
  rationale: string;
}

async function consumeSSE(
  url: string,
  body: string,
  onEvent: (type: string, data: Record<string, unknown>) => void,
): Promise<void> {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body,
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const chunk of parts) {
      if (!chunk.trim()) continue;
      const eventLine = chunk.split("\n").find((l) => l.startsWith("event:"));
      const dataLine = chunk.split("\n").find((l) => l.startsWith("data:"));
      if (!eventLine || !dataLine) continue;
      const eventType = eventLine.replace("event:", "").trim();
      const data = JSON.parse(dataLine.replace("data:", "").trim());
      onEvent(eventType, data);
    }
  }
}

export default function NewReportPage() {
  // Single-report state
  const [topic, setTopic] = useState("");
  const [domain, setDomain] = useState("general");
  const [manualTitle, setManualTitle] = useState("");
  const [manualText, setManualText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamEvents, setStreamEvents] = useState<{ type: string; data: Record<string, unknown> }[]>([]);
  const [completedReport, setCompletedReport] = useState<null | { id: number }>(null);
  const [error, setError] = useState("");

  // Batch state (consolidated single report)
  const [isBatchRunning, setIsBatchRunning] = useState(false);
  const [batchTopics, setBatchTopics] = useState<IdentifiedTopic[]>([]);
  const [batchStage, setBatchStage] = useState("");
  const [batchStreamedText, setBatchStreamedText] = useState("");
  const [batchTokens, setBatchTokens] = useState<number | null>(null);
  const [batchCost, setBatchCost] = useState<number | null>(null);
  const [batchReportId, setBatchReportId] = useState<number | null>(null);
  const [batchError, setBatchError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;

    setIsStreaming(true);
    setStreamEvents([]);
    setCompletedReport(null);
    setError("");

    const body = JSON.stringify({ topic, domain, manual_text: manualText, manual_title: manualTitle });

    try {
      await consumeSSE("http://localhost:8000/api/reports/generate", body, (eventType, data) => {
        setStreamEvents((prev) => [...prev, { type: eventType, data }]);
        if (eventType === "complete") setCompletedReport({ id: data.report_id as number });
        if (eventType === "error") setError((data.message as string) || "Unknown error");
      });
    } catch (err) {
      setError(String(err));
    } finally {
      setIsStreaming(false);
    }
  };

  const handleBatch = async () => {
    setIsBatchRunning(true);
    setBatchTopics([]);
    setBatchStage("identifying_topics");
    setBatchStreamedText("");
    setBatchTokens(null);
    setBatchCost(null);
    setBatchReportId(null);
    setBatchError("");

    const body = JSON.stringify({ days_lookback: 7, max_topics: 10 });

    try {
      await consumeSSE(
        "http://localhost:8000/api/reports/generate-batch",
        body,
        (eventType, data) => {
          if (eventType === "topics_identified") {
            setBatchTopics(data.topics as IdentifiedTopic[]);
          }
          if (eventType === "status") {
            setBatchStage((data.stage as string) || "");
          }
          if (eventType === "token") {
            setBatchStreamedText((prev) => prev + (data.text as string));
          }
          if (eventType === "complete") {
            setBatchReportId(data.report_id as number);
            setBatchTokens(data.tokens_used as number);
            setBatchCost(data.cost_usd as number);
          }
          if (eventType === "error") {
            setBatchError((data.message as string) || "Batch failed");
          }
        },
      );
    } catch (err) {
      setBatchError(String(err));
    } finally {
      setIsBatchRunning(false);
    }
  };

  const showBatchSection = isBatchRunning || batchTopics.length > 0 || batchReportId !== null;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Generate Intelligence Report</h1>

      <form onSubmit={handleSubmit} className="space-y-4 bg-gray-900 rounded-xl p-6 border border-gray-800">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Topic</label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g. Iran Strait of Hormuz closure risk, Taiwan Strait military activity"
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">Domain</label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
          >
            {DOMAINS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Article to Inject (optional)
          </label>
          <input
            type="text"
            value={manualTitle}
            onChange={(e) => setManualTitle(e.target.value)}
            placeholder="Article title"
            className="w-full px-3 py-2 mb-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <textarea
            value={manualText}
            onChange={(e) => setManualText(e.target.value)}
            placeholder="Paste article text here to include in the analysis..."
            rows={6}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
          />
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            type="submit"
            disabled={isStreaming || isBatchRunning || !topic.trim()}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
          >
            {isStreaming ? "Analyzing..." : "Analyze"}
          </button>

          <button
            type="button"
            onClick={handleBatch}
            disabled={isStreaming || isBatchRunning}
            className="px-6 py-2 bg-purple-700 hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
          >
            {isBatchRunning ? "Generating Top 10..." : "Generate Top 10"}
          </button>

          {!isBatchRunning && (
            <span className="text-xs text-gray-500">
              Scans last 7 days, generates 1 consolidated briefing on 10 topics
            </span>
          )}
        </div>
      </form>

      {showBatchSection && (
        <div className="space-y-3">
          <BatchProgress
            topics={batchTopics}
            stage={batchStage}
            streamedText={batchStreamedText}
            tokensUsed={batchTokens}
            costUsd={batchCost}
            completedReportId={batchReportId}
            isRunning={isBatchRunning}
          />
          {batchError && (
            <div className="p-4 bg-red-950 border border-red-800 rounded-xl text-red-300 text-sm">
              Batch error: {batchError}
            </div>
          )}
        </div>
      )}

      {(isStreaming || streamEvents.length > 0) && (
        <StreamingOutput events={streamEvents} isStreaming={isStreaming} />
      )}

      {error && (
        <div className="p-4 bg-red-950 border border-red-800 rounded-xl text-red-300">
          Error: {error}
        </div>
      )}

      {completedReport && (
        <div className="p-4 bg-green-950 border border-green-800 rounded-xl text-green-300">
          Report complete.{" "}
          <a href={`/reports/${completedReport.id}`} className="underline hover:text-green-200">
            View full report
          </a>
        </div>
      )}
    </div>
  );
}
