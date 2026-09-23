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
