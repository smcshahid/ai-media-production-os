/**
 * 4-stage pipeline stepper (Idea → Story → Script → Storyboard). In the Sprint 0
 * IDLE state every step renders as pending; once runs exist it highlights the
 * current stage and marks earlier stages done.
 */

const STAGE_LABELS: Record<string, string> = {
  IDEA: "Idea",
  STORY: "Story",
  SCRIPT: "Script",
  STORYBOARD: "Storyboard",
};

type StepState = "pending" | "active" | "done";

interface StepperProps {
  stages: string[];
  currentStage: string | null;
  status: string;
}

function stepState(index: number, currentIndex: number, status: string): StepState {
  if (status === "COMPLETED") {
    return "done";
  }
  if (status === "IDLE" || currentIndex < 0) {
    return "pending";
  }
  // Terminal failure: don't mark prior stages done — the run did not complete.
  if (status === "FAILED" || status === "CANCELLED") {
    return index === currentIndex ? "active" : "pending";
  }
  if (index < currentIndex) {
    return "done";
  }
  return index === currentIndex ? "active" : "pending";
}

export function Stepper({ stages, currentStage, status }: StepperProps) {
  const currentIndex = currentStage ? stages.indexOf(currentStage) : -1;

  return (
    <ol className="stepper" aria-label="Pipeline stages">
      {stages.map((stage, index) => {
        const state = stepState(index, currentIndex, status);
        return (
          <li key={stage} className={`stepper__step stepper__step--${state}`}>
            <span className="stepper__dot" aria-hidden="true">
              {index + 1}
            </span>
            <span className="stepper__label">{STAGE_LABELS[stage] ?? stage}</span>
          </li>
        );
      })}
    </ol>
  );
}
