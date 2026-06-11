import type { PipelineConnectionMode } from "../api/pipelineSocket";

interface PipelineConnectionIndicatorProps {
  mode: PipelineConnectionMode;
}

/** Live vs polling indicator for pipeline status (US-21 D-59). */
export function PipelineConnectionIndicator({ mode }: PipelineConnectionIndicatorProps) {
  if (mode === "connecting") {
    return (
      <span className="badge badge--idle pipeline-connection" title="Connecting to live updates">
        Connecting…
      </span>
    );
  }

  if (mode === "live") {
    return (
      <span className="badge badge--completed pipeline-connection" title="Receiving live updates">
        Live
      </span>
    );
  }

  return (
    <span className="badge badge--review pipeline-connection" title="Using REST polling fallback">
      Polling
    </span>
  );
}
