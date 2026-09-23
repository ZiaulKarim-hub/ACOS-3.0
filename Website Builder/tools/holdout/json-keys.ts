// PRD §22 — duplicate-key detection for a holdout pack's expected.json.
//
// Lives in its own file for ONE reason: so it can be property-tested directly,
// thousands of documents at a time, instead of only through a full reveal run.
// A QA review declined to clear it on inspection alone, and was right to.
//
// The problem it solves: JSON permits infinitely many spellings of one key.
// {"H1":…,"H\u0031":…} is a REPEATED key to JSON.parse, which keeps only the
// last value — so a holdout case can be graded against an expectation no human
// reading the file top-down would ever see. Two earlier guards searched the raw
// text for ONE literal spelling and were both defeated. This one never spells a
// key out: it tokenizes, decodes each key through JSON.parse, and compares
// decoded values within each object frame.

export const duplicateJsonKeys = (text: string): string[] => {
  const dupes = new Set<string>();
  const stack: Array<{ keys: Set<string>; isObject: boolean; expectKey: boolean }> = [];
  let i = 0;
  while (i < text.length) {
    const ch = text[i];
    if (ch === '"') {
      let j = i + 1;                       // find the end of the string token
      while (j < text.length) {
        if (text[j] === "\\") { j += 2; continue; }   // an escaped char, whatever it is
        if (text[j] === '"') break;
        j++;
      }
      const top = stack[stack.length - 1];
      if (top && top.isObject && top.expectKey) {
        const token = text.slice(i, j + 1);
        let decoded: string;
        try { decoded = JSON.parse(token) as string; } catch { decoded = token; }
        if (top.keys.has(decoded)) dupes.add(decoded);
        top.keys.add(decoded);
        top.expectKey = false;             // next is ":" then a VALUE, not a key
      }
      i = j + 1;
      continue;
    }
    if (ch === "{") { stack.push({ keys: new Set(), isObject: true, expectKey: true }); i++; continue; }
    if (ch === "[") { stack.push({ keys: new Set(), isObject: false, expectKey: false }); i++; continue; }
    if (ch === "}" || ch === "]") { stack.pop(); i++; continue; }
    if (ch === ",") { const t = stack[stack.length - 1]; if (t?.isObject) t.expectKey = true; i++; continue; }
    i++;
  }
  return [...dupes];
};

/**
 * F9 (security review): the duplicate-key defence covered expected.json but not
 * cases.yaml — and Bun.YAML.parse keeps the LAST duplicate key in silence, MEASURED:
 * a case carrying `run:` twice showed a reader one command and executed the other.
 * The same defect class as duplicateJsonKeys closes, one file over.
 *
 * Scope, stated: block-style case lists only, which is the only shape seal.ts
 * documents. Quoted key spellings ("run": / 'run':) are matched as the bare
 * key, because YAML resolves them to the same key (V2, executed). Flow-style case mappings ("- { id: H1, run: a, run: b }") are refused
 * outright rather than scanned, and a block scalar ("run: |") is refused because
 * its continuation lines are indistinguishable from keys to a line scanner. A
 * false refusal costs a re-seal; a missed duplicate costs a spent pack.
 */
export const CASE_KEYS = ["id", "class", "description", "run"] as const;
export const caseKeyProblems = (text: string): string[] => {
  const problems: string[] = [];
  const lines = text.split("\n");
  let block: Array<{ line: string; at: number }> = [];
  let blockStart = 0;
  const flush = () => {
    if (!block.length) return;
    for (const key of CASE_KEYS) {
      // The keys are compile-time literals, never user input — nothing to escape.
      // V2 (fifth security review, EXECUTED): `"run":` and `'run':` resolve to
      // the SAME key as bare `run:` in Bun.YAML — and the old pattern matched
      // only the bare spelling, so a pack carrying `run:` and `"run":` sealed
      // without complaint and executed the second. Quoted spellings count too,
      // exactly as duplicateJsonKeys already decodes them on the JSON side.
      const hits = block.filter((b) => new RegExp(`^\\s*(?:-\\s+)?["']?${key}["']?\\s*:`).test(b.line)).length;
      if (hits > 1) {
        problems.push(`the case starting at line ${blockStart + 1} carries "${key}:" ${hits} times — YAML keeps only the LAST one, so a reader and the harness would disagree about this case`);
      }
    }
    block = [];
  };
  lines.forEach((line, i) => {
    // W3 (sixth security review, EXECUTED): the old pattern caught only "- {"
    // on one line. `cases: [{...}]`, a dash on its own line, and a multi-line
    // flow mapping all bypassed it — and a one-line flow pack carrying run:
    // twice SEALED and executed the second command. Any line whose structure
    // OPENS a flow collection is refused: first non-space char "{" or "[",
    // "- {" / "- [", or a key ending in "[" or "{". Braces INSIDE a quoted
    // run string sit after `run: "` and never match these shapes. This scan
    // is now belt-and-braces anyway: reveal requires the file to BE the
    // canonical serialization of its own parse (canonicalCasesText below),
    // which no flow spelling can satisfy.
    if (/^\s*[\{\[]/.test(line) || /^\s*-\s*[\{\[]/.test(line) || /:\s*[\{\[]/.test(line)) {
      problems.push(`line ${i + 1}: flow-style collections ("{...}" / "[...]") are refused in cases.yaml structure — a repeated key inside one is invisible to a line scan`);
    }
    if (/:\s*[|>]/.test(line)) {
      problems.push(`line ${i + 1}: block scalars ("|" or ">") are refused — their continuation lines are indistinguishable from keys to this scan`);
    }
    if (/^\s*-\s/.test(line)) { flush(); blockStart = i; }
    block.push({ line, at: i });
  });
  flush();
  return problems;
};

/**
 * W3, the structural half: the sealed cases.yaml must BE the canonical
 * serialization of its own parse. seal.ts rewrites the authored file into this
 * form; reveal.ts regenerates it from the parsed value and refuses on any byte
 * of difference. Consequence: "a reader sees X, the harness runs Y" is
 * impossible in a sealed pack, whatever the YAML spelling — three consecutive
 * review passes defeated line regexes with spellings nobody enumerated, and
 * this closes the CLASS. Values are JSON-encoded (escapes fully defined, one
 * line by construction); comments are dropped (the README carries prose);
 * unknown case keys are refused at seal, so nothing is silently lost.
 */
export const CANON_HEADER = "# canonical form wb-cases-1 — regenerated by seal.ts; reveal refuses any deviation";
export function canonicalCasesText(casesText: string): string {
  const doc = (globalThis as any).Bun.YAML.parse(casesText) as { cases: Array<Record<string, unknown>> };
  if (!doc || !Array.isArray(doc.cases)) throw new Error("cases.yaml does not hold a cases: list");
  const out = [CANON_HEADER, "cases:"];
  for (const c of doc.cases) {
    out.push(`  - id: ${JSON.stringify(String(c.id))}`);
    out.push(`    class: ${JSON.stringify(String(c.class))}`);
    if (c.description !== undefined) out.push(`    description: ${JSON.stringify(String(c.description))}`);
    out.push(`    run: ${JSON.stringify(String(c.run))}`);
  }
  return out.join("\n") + "\n";
}
