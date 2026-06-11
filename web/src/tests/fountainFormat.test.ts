import { describe, expect, it } from "vitest";

import { formatFountainHtml } from "../lib/fountainFormat";

const SAMPLE = `Title: US-14 OLARES VERIFY

INT. RESEARCH LAB - DAWN

The lab is dimly lit.

DR. ELARA VOSS
(whispering)
If I send this...
`;

describe("formatFountainHtml", () => {
  it("renders scene heading, action, character, and dialogue", () => {
    const html = formatFountainHtml(SAMPLE);
    expect(html).toContain('class="fountain-scene"');
    expect(html).toContain("INT. RESEARCH LAB - DAWN");
    expect(html).toContain('class="fountain-action"');
    expect(html).toContain('class="fountain-character"');
    expect(html).toContain("DR. ELARA VOSS");
    expect(html).toContain('class="fountain-dialogue"');
    expect(html).toContain("If I send this...");
  });

  it("escapes HTML in fountain text", () => {
    const html = formatFountainHtml("INT. LAB - DAY\n\n<script>alert(1)</script>");
    expect(html).not.toContain("<script>");
    expect(html).toContain("&lt;script&gt;");
  });

  it("returns empty string for blank input", () => {
    expect(formatFountainHtml("   ")).toBe("");
  });
});
