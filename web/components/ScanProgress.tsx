"use client";

import { useEffect, useRef, useState } from "react";
import type { ScanProgressEvent } from "@/lib/types";

interface Props {
  jobId: string;
  onComplete: () => void;
}

export function ScanProgress({ jobId, onComplete }: Props) {
  const [events, setEvents] = useState<ScanProgressEvent[]>([]);
  const [current, setCurrent] = useState<ScanProgressEvent | null>(null);
  const [done, setDone] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const es = new EventSource(`/api/jobs/${jobId}/stream`, {
      withCredentials: true,
    });

    es.onmessage = (e: MessageEvent) => {
      const event: ScanProgressEvent = JSON.parse(e.data as string);
      if (event.type === "done") {
        setDone(true);
        es.close();
        onComplete();
        return;
      }
      setCurrent(event);
      setEvents((prev) => [...prev.slice(-49), event]);
    };

    es.onerror = () => {
      es.close();
      setDone(true);
      onComplete();
    };

    return () => es.close();
  }, [jobId, onComplete]);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events]);

  const progressPercent =
    current?.count && current?.total
      ? Math.round((current.count / current.total) * 100)
      : null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {!done ? (
          <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent" />
        ) : (
          <span className="inline-block h-3 w-3 rounded-full bg-green-400" />
        )}
        <span className="text-sm text-gray-300">
          {done
            ? "Scan complete."
            : current?.site
            ? `Checking ${current.site}…`
            : "Starting…"}
        </span>
        {progressPercent !== null && !done && (
          <span className="ml-auto text-xs text-muted">
            {current?.count} / {current?.total}
          </span>
        )}
      </div>

      {progressPercent !== null && !done && (
        <div className="h-1.5 w-full rounded-full bg-gray-800">
          <div
            className="h-1.5 rounded-full bg-accent transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      )}

      <div
        ref={containerRef}
        className="h-48 overflow-y-auto rounded-lg border border-border bg-panel p-3 font-mono text-xs text-gray-400 space-y-0.5"
      >
        {events.map((e, i) => (
          <div key={i} className="flex gap-2">
            <span className="text-muted">{e.source}</span>
            <span className="text-gray-300">{e.site}</span>
            <span
              className={
                e.status === "found"
                  ? "text-red-400"
                  : e.status === "not_found"
                  ? "text-gray-500"
                  : "text-yellow-400"
              }
            >
              {e.status}
            </span>
          </div>
        ))}
        {done && (
          <div className="text-green-400 mt-1">— scan finished —</div>
        )}
      </div>
    </div>
  );
}
