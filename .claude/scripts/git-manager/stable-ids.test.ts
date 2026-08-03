// Proves the one property the whole module exists for: a project's printed
// number does not move when its state changes, when the sort order changes, or
// when other projects appear and disappear around it.
//
//   bun .claude/scripts/git-manager/stable-ids.test.ts

import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { assignStableIds, highestId, loadIds } from "./stable-ids.ts";

const out: string[] = [];
let failed = 0;
const ok = (name: string, cond: unknown, note = "") => {
  if (!cond) failed++;
  out.push(`${cond ? "PASS" : "FAIL"}  ${name}${cond ? "" : `  — ${note}`}`);
};

const dir = mkdtempSync(join(tmpdir(), "gm-ids-"));
const FILE = join(dir, "ids.json");
const row = (path: string) => ({ path, index: 0 });

try {
  // 1. first run seeds 1..N in display order
  const first = [row("/a"), row("/b"), row("/c")];
  const r1 = assignStableIds(first, FILE);
  ok("first run numbers rows 1..N in display order",
    first.map((r) => r.index).join(",") === "1,2,3", first.map((r) => r.index).join(","));
  ok("registry file written", existsSync(FILE));
  ok("all three reported as newly minted", r1.minted.length === 3, String(r1.minted.length));

  // 2. THE POINT: re-sorting must not renumber
  const reordered = [row("/c"), row("/a"), row("/b")];
  assignStableIds(reordered, FILE);
  ok("a different sort order does NOT renumber",
    reordered.map((r) => `${r.path}=${r.index}`).join(" ") === "/c=3 /a=1 /b=2",
    reordered.map((r) => `${r.path}=${r.index}`).join(" "));

  // 3. a row leaving (e.g. it got committed and dropped out of the view) must
  //    not shift the rows that remain — the exact 2026-08-02 failure
  const afterCommit = [row("/a"), row("/c")];
  assignStableIds(afterCommit, FILE);
  ok("a row disappearing does not shift the others",
    afterCommit.map((r) => r.index).join(",") === "1,3", afterCommit.map((r) => r.index).join(","));

  // 4. a new project takes max+1, never a retired number
  const withNew = [row("/a"), row("/b"), row("/c"), row("/d")];
  const r4 = assignStableIds(withNew, FILE);
  ok("a new project takes the next unused number",
    withNew.find((r) => r.path === "/d")!.index === 4, String(withNew.find((r) => r.path === "/d")!.index));
  ok("only the new project is reported as minted",
    r4.minted.length === 1 && r4.minted[0].path === "/d", JSON.stringify(r4.minted));

  // 5. numbers are never recycled: retire /b, add /e
  const retired = [row("/a"), row("/c"), row("/d"), row("/e")];
  assignStableIds(retired, FILE);
  ok("a retired number is NOT handed to a new project",
    retired.find((r) => r.path === "/e")!.index === 5,
    `/e got ${retired.find((r) => r.path === "/e")!.index}, /b still holds 2`);
  ok("the retired path keeps its entry so its number stays spent",
    loadIds(FILE).ids.get("/b") === 2, String(loadIds(FILE).ids.get("/b")));

  // 6. /b coming back gets its ORIGINAL number
  const returned = [row("/b")];
  assignStableIds(returned, FILE);
  ok("a project that comes back gets its original number", returned[0].index === 2,
    String(returned[0].index));

  // 7. a pure re-scan must not rewrite the file
  const before = Bun.file(FILE).lastModified;
  await Bun.sleep(15);
  const again = assignStableIds([row("/a"), row("/b")], FILE);
  ok("a re-scan with nothing new does not rewrite the registry",
    again.minted.length === 0 && Bun.file(FILE).lastModified === before);

  // 8. highest id tracks retired entries too
  ok("highestId counts retired paths", highestId(loadIds(FILE).ids) === 5,
    String(highestId(loadIds(FILE).ids)));

  // 9. a corrupt registry must THROW, never silently renumber everything
  writeFileSync(FILE, "{ this is not json");
  let threw = false;
  try { assignStableIds([row("/a")], FILE); } catch { threw = true; }
  ok("a corrupt registry throws instead of renumbering everything", threw);
} finally {
  rmSync(dir, { recursive: true, force: true });
}

for (const line of out) console.log(line);
console.log(`\n${out.length - failed}/${out.length} passed`);
if (failed) process.exit(1);
