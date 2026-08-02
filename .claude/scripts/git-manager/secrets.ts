// git-manager — pre-push secret scan.
//
// Looks at the lines a push would ADD and flags anything that looks like a
// credential. This is the one mistake that survives deletion: a key pushed to a
// place other people can reach must be treated as exposed and rotated, whether
// or not the commit is later removed.
//
// Findings are always MASKED. The tool must never reprint the secret it found —
// doing so would copy it into the transcript, which is one more place it lives.
//
// This is a net, not a proof. It catches shaped credentials; it cannot catch a
// password that looks like an ordinary word.

export interface SecretHit {
  file: string;
  line: number;
  rule: string;
  masked: string;
}

interface Rule {
  name: string;
  re: RegExp;
  /** Which capture group holds the secret value; 0 = whole match. */
  group?: number;
}

const RULES: Rule[] = [
  { name: "Anthropic API key", re: /\bsk-ant-[A-Za-z0-9_-]{20,}/ },
  { name: "OpenAI-style API key", re: /\bsk-[A-Za-z0-9]{32,}/ },
  { name: "GitHub personal access token", re: /\bghp_[A-Za-z0-9]{36}\b/ },
  { name: "GitHub fine-grained token", re: /\bgithub_pat_[A-Za-z0-9_]{50,}/ },
  { name: "GitHub OAuth token", re: /\bgho_[A-Za-z0-9]{36}\b/ },
  { name: "AWS access key id", re: /\bAKIA[0-9A-Z]{16}\b/ },
  { name: "Google API key", re: /\bAIza[0-9A-Za-z_-]{35}\b/ },
  { name: "Slack token", re: /\bxox[baprs]-[A-Za-z0-9-]{10,}/ },
  { name: "Stripe secret key", re: /\b(?:sk|rk)_live_[A-Za-z0-9]{20,}/ },
  { name: "private key block", re: /-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----/ },
  { name: "JSON web token", re: /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}/ },
  {
    name: "assigned secret value",
    re: /\b(?:api[_-]?key|apikey|secret|password|passwd|token|access[_-]?key|client[_-]?secret)\b\s*[:=]\s*["'`]([^"'`\n]{16,})["'`]/i,
    group: 1,
  },
];

/**
 * Values that merely LOOK like assignments but carry no secret: placeholders,
 * environment lookups, template holes. Without this the generic rule fires on
 * every config file and the warning stops meaning anything.
 */
const PLACEHOLDER =
  /^(?:\$|\{|<|process\.|env\.|os\.|import\.meta|["'`]?\s*$)|(?:xxx|your[-_]|changeme|example|placeholder|redacted|dummy|sample|test[-_]?key|fake|todo|n\/a|\*{4,})/i;

/** Show enough to find it, never enough to use it. */
export function mask(value: string): string {
  if (value.length <= 8) return "*".repeat(value.length);
  return `${value.slice(0, 4)}${"*".repeat(Math.min(24, value.length - 8))}${value.slice(-4)} (${
    value.length
  } chars)`;
}

/** Files whose contents are noise for this purpose. */
function skipFile(file: string): boolean {
  return (
    /(?:^|\/)(?:package-lock\.json|bun\.lockb|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock)$/.test(file) ||
    /(?:^|\/)node_modules\//.test(file) ||
    /\.(?:png|jpe?g|gif|pdf|zip|woff2?|ttf|otf|mp4|mov|ico|icns)$/i.test(file)
  );
}

export function scanForSecrets(
  lines: { file: string; line: number; text: string }[],
): SecretHit[] {
  const hits: SecretHit[] = [];
  const seen = new Set<string>();

  for (const { file, line, text } of lines) {
    if (skipFile(file)) continue;
    if (text.length > 4000) continue; // minified bundle, not hand-written config

    for (const rule of RULES) {
      const m = text.match(rule.re);
      if (!m) continue;
      const value = rule.group ? m[rule.group] : m[0];
      if (!value) continue;
      if (rule.group && PLACEHOLDER.test(value)) continue;

      const key = `${file}:${line}:${rule.name}`;
      if (seen.has(key)) continue;
      seen.add(key);
      hits.push({ file, line, rule: rule.name, masked: mask(value) });
      break; // one finding per line is enough to stop the push
    }
  }
  return hits;
}
