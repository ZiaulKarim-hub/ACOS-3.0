/**
 * record-format.ts — the run record's trust regions (security review T2).
 *
 * EXECUTED defeat this closes: reveal.ts wrote `run: ${c.run}` verbatim into
 * the hashed log, and verify-run-records.ts read every field with a
 * first-match line scan over the WHOLE document. Case sections precede the
 * footer, so a case `run` string carrying an escaped newline (a double-quoted
 * YAML scalar — legal, and invisible to the block-scalar refusals) injected
 * `post_run_pack_untouched: true` ABOVE the real `false`. The raw log hash
 * still verified — nothing was edited after sealing; the forgery was written
 * BY the sealer, at run time. One sed on the unhashed manifest later, the
 * verifier blessed the lie.
 *
 * The fix is structural, not cosmetic: the log has three regions, and only
 * two are trusted.
 *
 *   header  = start ....... first CASES_DELIM line     (written before any case runs)
 *   cases   = in between                               (CANDIDATE-CONTROLLED; never parsed for fields)
 *   footer  = last FOOTER_DELIM line ....... EOF       (written after the last case)
 *
 * A case cannot write above the header's end (it does not exist yet when the
 * header is emitted... it exists on disk only after the footer is appended —
 * the whole log is buffered in memory and written once). It CAN echo either
 * delimiter into its own `run` string; that copy sits in the cases region, so
 * "first CASES_DELIM" and "LAST FOOTER_DELIM" still bound the trusted spans.
 * Belt and braces on top: newlines are refused in every case string field at
 * seal AND reveal, and `run` is JSON-escaped in the log.
 */

export const CASES_DELIM = "=== cases: candidate-controlled region — no field below this line is trusted until the footer delimiter ===";
export const FOOTER_DELIM = "=== wb-run-record footer v2: authoritative fields run from the LAST occurrence of this line to end-of-file ===";

/** The trusted spans, or null when a delimiter is missing (pre-T2 or forged log). */
export function trustedRegions(logText: string): { header: string; footer: string } | null {
  const lines = logText.split("\n");
  const firstCases = lines.indexOf(CASES_DELIM);
  const lastFooter = lines.lastIndexOf(FOOTER_DELIM);
  if (firstCases < 0 || lastFooter < 0 || lastFooter < firstCases) return null;
  return {
    header: lines.slice(0, firstCases).join("\n"),
    footer: lines.slice(lastFooter + 1).join("\n"),
  };
}
