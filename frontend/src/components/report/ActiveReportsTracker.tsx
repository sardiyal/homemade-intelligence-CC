"use client";

interface ActiveReport {
  id: number;
  topic: string;
  domain: string | null;
  status: string;
  created_at: string | null;
  has_active_pipeline: boolean;
}

const DOMAIN_COLORS: Record<string, string> = {
  geopolitics: "bg-red-900 text-red-300",
  markets: "bg-green-900 text-green-300",
  taiwan: "bg-blue-900 text-blue-300",
  energy: "bg-yellow-900 text-yellow-300",
  general: "bg-gray-800 text-gray-300",
};

function elapsedSince(isoString: string): string {
  const diff = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000);
  if (diff < 60) return `${diff}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ${diff % 60}s`;
  return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
}

export default function ActiveReportsTracker({ reports }: { reports: ActiveReport[] }) {
  if (!Array.isArray(reports) || reports.length === 0) return null;

  return (
    <div className="border border-yellow-800 bg-yellow-950/30 rounded-xl p-4 space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium text-yellow-300">
        <span className="inline-block w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
        {reports.length === 1 ? "1 report generating" : `${reports.length} reports generating`}
      </div>

      <div className="space-y-2">
        {reports.map((r) => (
          <div key={r.id} className="flex items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-2 min-w-0">
              <span
                className={`px-2 py-0.5 rounded-full text-xs flex-shrink-0 ${
                  DOMAIN_COLORS[r.domain || "general"] ?? DOMAIN_COLORS.general
                }`}
              >
                {r.domain || "general"}
              </span>
              <span className="text-gray-300 truncate">{r.topic}</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0 text-gray-500 text-xs">
              {r.has_active_pipeline && (
                <span className="text-yellow-400 animate-pulse">●</span>
              )}
              {r.created_at && <span>{elapsedSince(r.created_at)}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
