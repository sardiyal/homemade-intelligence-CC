"use client";

interface IdentifiedTopic {
  topic: string;
  domain: string;
  rationale: string;
}

interface BatchProgressProps {
  topics: IdentifiedTopic[];
  stage: string;
  streamedText: string;
  tokensUsed: number | null;
  costUsd: number | null;
  completedReportId: number | null;
  isRunning: boolean;
}

const DOMAIN_COLORS: Record<string, string> = {
  geopolitics: "bg-red-900 text-red-300",
  markets: "bg-green-900 text-green-300",
  taiwan: "bg-blue-900 text-blue-300",
  energy: "bg-yellow-900 text-yellow-300",
  general: "bg-gray-800 text-gray-300",
};

const STAGE_LABELS: Record<string, string> = {
  identifying_topics: "Identifying top topics...",
  ingest: "Retrieving source content...",
  triangulate: "Analyzing bias coverage...",
  analyze: "Generating consolidated analysis...",
  format: "Formatting for audiences...",
};

export default function BatchProgress({
  topics,
  stage,
  streamedText,
  tokensUsed,
  costUsd,
  completedReportId,
  isRunning,
}: BatchProgressProps) {
  return (
    <div className="space-y-4 bg-gray-900 border border-gray-800 rounded-xl p-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {isRunning ? (
            <span className="inline-block w-2 h-2 rounded-full bg-purple-400 animate-pulse" />
          ) : completedReportId ? (
            <span className="inline-block w-2 h-2 rounded-full bg-green-400" />
          ) : (
            <span className="inline-block w-2 h-2 rounded-full bg-gray-500" />
          )}
          <span className="font-medium text-sm">
            {completedReportId
              ? "Consolidated briefing complete"
              : isRunning
                ? STAGE_LABELS[stage] || stage
                : "Top 10 Intelligence Briefing"}
          </span>
        </div>
        {(tokensUsed != null || costUsd != null) && (
          <span className="text-xs text-gray-400">
            {tokensUsed != null && <span>{tokensUsed.toLocaleString()} tokens</span>}
            {costUsd != null && <span className="ml-2">${costUsd.toFixed(4)}</span>}
          </span>
        )}
      </div>

      {/* Topics list */}
      {topics.length > 0 && (
        <div className="space-y-1.5">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Topics identified</p>
          <div className="space-y-1">
            {topics.map((t, i) => (
              <div key={i} className="flex items-start gap-2 text-sm">
                <span className="text-gray-500 font-mono w-5 flex-shrink-0 text-right">{i + 1}.</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-xs flex-shrink-0 ${
                    DOMAIN_COLORS[t.domain] ?? DOMAIN_COLORS.general
                  }`}
                >
                  {t.domain}
                </span>
                <span className="text-gray-300 line-clamp-1">{t.topic}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Streaming analysis preview */}
      {streamedText && stage === "analyze" && isRunning && (
        <div className="mt-3 pt-3 border-t border-gray-800">
          <p className="text-xs text-gray-500 mb-2">Analysis preview:</p>
          <div className="max-h-48 overflow-y-auto text-sm text-gray-400 whitespace-pre-wrap font-mono">
            {streamedText.slice(-1000)}
          </div>
        </div>
      )}

      {/* Completed link */}
      {completedReportId && (
        <div className="pt-3 border-t border-gray-800">
          <a
            href={`/reports/${completedReportId}`}
            className="inline-block px-4 py-2 bg-blue-700 hover:bg-blue-600 text-sm rounded-lg transition-colors"
          >
            View Consolidated Briefing
          </a>
        </div>
      )}
    </div>
  );
}
