/** Line-based text diff for read-only Story/Script version comparison (Phase 3B / US-30). */

export type DiffLineKind = "same" | "added" | "removed";

export interface DiffLine {
  kind: DiffLineKind;
  text: string;
  leftLine: number | null;
  rightLine: number | null;
}

/**
 * Simple LCS line diff — sufficient for treatment/script prose comparison.
 */
export function diffLines(left: string, right: string): DiffLine[] {
  const leftLines = left.replace(/\r\n/g, "\n").split("\n");
  const rightLines = right.replace(/\r\n/g, "\n").split("\n");
  const lcs = buildLcsTable(leftLines, rightLines);
  const raw = backtrack(leftLines, rightLines, lcs);
  return annotateLineNumbers(raw);
}

function buildLcsTable(a: string[], b: string[]): number[][] {
  const rows = a.length + 1;
  const cols = b.length + 1;
  const table: number[][] = Array.from({ length: rows }, () => Array(cols).fill(0));
  for (let i = 1; i < rows; i += 1) {
    for (let j = 1; j < cols; j += 1) {
      if (a[i - 1] === b[j - 1]) {
        table[i][j] = table[i - 1][j - 1] + 1;
      } else {
        table[i][j] = Math.max(table[i - 1][j], table[i][j - 1]);
      }
    }
  }
  return table;
}

function backtrack(
  a: string[],
  b: string[],
  table: number[][],
): Array<{ kind: DiffLineKind; text: string }> {
  const result: Array<{ kind: DiffLineKind; text: string }> = [];
  let i = a.length;
  let j = b.length;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && a[i - 1] === b[j - 1]) {
      result.unshift({ kind: "same", text: a[i - 1] });
      i -= 1;
      j -= 1;
    } else if (j > 0 && (i === 0 || table[i][j - 1] >= table[i - 1][j])) {
      result.unshift({ kind: "added", text: b[j - 1] });
      j -= 1;
    } else {
      result.unshift({ kind: "removed", text: a[i - 1] });
      i -= 1;
    }
  }
  return result;
}

function annotateLineNumbers(raw: Array<{ kind: DiffLineKind; text: string }>): DiffLine[] {
  let left = 0;
  let right = 0;
  return raw.map((line) => {
    if (line.kind === "same") {
      left += 1;
      right += 1;
      return { ...line, leftLine: left, rightLine: right };
    }
    if (line.kind === "removed") {
      left += 1;
      return { ...line, leftLine: left, rightLine: null };
    }
    right += 1;
    return { ...line, leftLine: null, rightLine: right };
  });
}

/** True when any line differs between two text bodies. */
export function textsDiffer(left: string, right: string): boolean {
  return left !== right;
}
