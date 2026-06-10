import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Stepper } from "../components/Stepper";

const STAGES = ["IDEA", "STORY", "SCRIPT", "STORYBOARD"];

describe("Stepper", () => {
  it("renders all four stage labels", () => {
    render(<Stepper stages={STAGES} currentStage={null} status="IDLE" />);
    for (const label of ["Idea", "Story", "Script", "Storyboard"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("marks every step pending when idle", () => {
    const { container } = render(<Stepper stages={STAGES} currentStage={null} status="IDLE" />);
    expect(container.querySelectorAll(".stepper__step--pending")).toHaveLength(4);
    expect(container.querySelectorAll(".stepper__step--active")).toHaveLength(0);
  });

  it("highlights the current stage and marks earlier stages done", () => {
    const { container } = render(
      <Stepper stages={STAGES} currentStage="SCRIPT" status="RUNNING" />,
    );
    expect(container.querySelectorAll(".stepper__step--done")).toHaveLength(2);
    expect(container.querySelectorAll(".stepper__step--active")).toHaveLength(1);
  });

  it("marks all stages done when pipeline is completed", () => {
    const { container } = render(
      <Stepper stages={STAGES} currentStage="STORYBOARD" status="COMPLETED" />,
    );
    expect(container.querySelectorAll(".stepper__step--done")).toHaveLength(4);
    expect(container.querySelectorAll(".stepper__step--active")).toHaveLength(0);
  });
});
