/**
 * Presentation mapping for dashboard (US-10). API/DB values are unchanged (D-32).
 */

export type PipelineDisplayStatus =
  | "IDLE"
  | "GENERATING"
  | "REVIEW"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | string;

/** Map `pipeline_runs.status` (or IDLE sentinel) to dashboard labels. */
export function toDisplayStatus(apiStatus: string): PipelineDisplayStatus {
  switch (apiStatus) {
    case "IDLE":
      return "IDLE";
    case "RUNNING":
    case "PENDING":
      return "GENERATING";
    case "AWAITING_APPROVAL":
      return "REVIEW";
    case "COMPLETED":
      return "COMPLETED";
    case "FAILED":
      return "FAILED";
    case "CANCELLED":
      return "CANCELLED";
    default:
      return apiStatus;
  }
}

export function isPipelineActive(apiStatus: string): boolean {
  return apiStatus === "RUNNING" || apiStatus === "AWAITING_APPROVAL" || apiStatus === "PENDING";
}

export function canStartPipeline(apiStatus: string): boolean {
  return !isPipelineActive(apiStatus);
}

/** Poll every 5s while generating or awaiting review (US-10 AC). */
export function pipelinePollIntervalMs(apiStatus: string | null): number {
  if (apiStatus === "RUNNING" || apiStatus === "AWAITING_APPROVAL" || apiStatus === "PENDING") {
    return 5000;
  }
  return 15000;
}

export function badgeClassForStatus(displayStatus: PipelineDisplayStatus): string {
  if (displayStatus === "IDLE") {
    return "badge--idle";
  }
  if (displayStatus === "COMPLETED") {
    return "badge--completed";
  }
  if (displayStatus === "REVIEW") {
    return "badge--review";
  }
  if (displayStatus === "GENERATING") {
    return "badge--generating";
  }
  return "badge--active";
}
