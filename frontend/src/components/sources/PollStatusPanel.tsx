"use client";

import { useState } from "react";

interface PollResult {
  source_name: string;
  new_articles: number;
  polled_at: string;
}

interface PollStatus {
  last_poll_started: string | null;
  last_poll_completed: string | null;
  last_poll_duration_seconds: number | null;
  is_polling: boolean;
  total_polls: number;
  next_scheduled_poll: string | null;
  results: PollResult[];
}

function timeAgo(isoString: string): string {
  const diff = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

function timeUntil(isoString: string): string {
  const diff = Math.floor((new Date(isoString).getTime() - Date.now()) / 1000);
  if (diff <= 0) return "imminent";
  if (diff < 60) return `in ${diff}s`;
  if (diff < 3600) return `in ${Math.floor(diff / 60)}m`;
  return `in ${Math.floor(diff / 3600)}h`;
}

export default function PollStatusPanel({ status }: { status: PollStatus | null }) {
  const [expanded, setExpanded] = useState(false);

  if (!status) return null;

  const totalNew = status.results.reduce((sum, r) => sum + r.new_articles, 0);

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 text-sm">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {status.is_polling ? (
            <span className="flex items-center gap-2 text-yellow-400">
              <span className="inline-block w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
              Polling RSS feeds...
            </span>
          ) : (
            <span className="flex items-center gap-2 text-green-400">
              <span className="inline-block w-2 h-2 rounded-full bg-green-400" />
              RSS idle
            </span>
          )}

          {status.last_poll_completed && (
            <span className="text-gray-400">
              Last poll:{" "}
              <span className="text-gray-200">{timeAgo(status.last_poll_completed)}</span>
              {status.last_poll_duration_seconds != null && (
                <span className="text-gray-500"> ({status.last_poll_duration_seconds}s)</span>
              )}
              {status.total_polls > 0 && (
                <span className="text-gray-500 ml-1">— {totalNew} new articles</span>
              )}
            </span>
          )}

          {status.next_scheduled_poll && (
            <span className="text-gray-500">
              Next: <span className="text-gray-300">{timeUntil(status.next_scheduled_poll)}</span>
            </span>
          )}
        </div>

        {status.results.length > 0 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            {expanded ? "Hide sources" : `Show ${status.results.length} sources`}
          </button>
        )}
      </div>

      {expanded && status.results.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-800 grid grid-cols-2 gap-1 max-h-48 overflow-y-auto">
          {status.results.map((r) => (
            <div key={r.source_name} className="flex items-center justify-between px-2 py-1 rounded bg-gray-800">
              <span className="text-gray-300 truncate max-w-[160px]">{r.source_name}</span>
              <span className={`ml-2 text-xs font-mono ${r.new_articles > 0 ? "text-green-400" : "text-gray-500"}`}>
                +{r.new_articles}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
