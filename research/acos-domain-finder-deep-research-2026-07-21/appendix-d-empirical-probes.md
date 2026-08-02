# Appendix D — Main-session empirical probe transcripts (2026-07-21, ~04:45–05:15 UTC 2026-07-22)

All probes run via curl / raw port-43 sockets from the main session (independent of Agent 1's probes — two evidence classes).

## D1. IANA bootstrap coverage check (data.iana.org/rdap/dns.json, publication 2026-07-14T22:00:03Z, 1199 TLDs)
```
com/net/org/ai/app/dev/xyz/tech/uk/ca/in/id/site/online/store/cloud/fun/page/link/club/shop -> RDAP base present
io/co/me/us/de/sh/gg/so -> NO RDAP IN BOOTSTRAP
```

## D2. Bootstrap-listed RDAP endpoints — 200/404 semantics (8/8 TLDs correct)
```
com nic.com -> HTTP 200
com qzxv93k7blorptun.com -> HTTP 404
ai nic.ai -> HTTP 200
ai qzxv93k7blorptun.ai -> HTTP 404
app nic.app -> HTTP 200
app qzxv93k7blorptun.app -> HTTP 404
dev nic.dev -> HTTP 200
dev qzxv93k7blorptun.dev -> HTTP 404
xyz nic.xyz -> HTTP 200
xyz qzxv93k7blorptun.xyz -> HTTP 404
tech nic.tech -> HTTP 200
tech qzxv93k7blorptun.tech -> HTTP 404
uk nic.uk -> HTTP 200
uk qzxv93k7blorptun.uk -> HTTP 404
org nic.org -> HTTP 200
org qzxv93k7blorptun.org -> HTTP 404
---- rdap.org redirector on NON-bootstrap TLDs ----
rdap.org nic.io -> HTTP 404 (following redirects)
rdap.org nic.co -> HTTP 404 (following redirects)
rdap.org nic.me -> HTTP 000 (following redirects)
```

## D3. WHOIS port-43 fallback probes
```
io  TAKEN nic.io    via whois.nic.io    -> full record   | FREE qzxv93k7blorptun.io -> 'Domain not found.'
me  TAKEN nic.me    via whois.nic.me    -> full record   | FREE -> 'Domain not found.'
sh  TAKEN nic.sh    via whois.nic.sh    -> full record   | FREE -> 'Domain not found.'
us  TAKEN nic.us    via whois.nic.us    -> full record   | FREE -> 'No Data Found'
de  TAKEN denic.de  via whois.denic.de  -> 'Status: connect' | FREE -> 'Status: free'  (query format: -T dn <domain>)
co  whois.nic.co    -> DNS resolution failure (Errno 8). IANA referral (whois.iana.org co) -> whois: whois.registry.co
co  TAKEN nic.co    via whois.registry.co -> full record | FREE -> 'The queried object does not exist: DOMAIN NOT FOUND'
```

## D4. Cross-verification of Agent 1's non-bootstrap ('shadow RDAP') override endpoints — 14/14 correct
```
io  TAKEN nic.io                -> HTTP 200
io  FREE  qzxv93k7blorptun.io   -> HTTP 404
me  TAKEN domain.me             -> HTTP 200
me  FREE  qzxv93k7blorptun.me   -> HTTP 404
sh  TAKEN nic.sh                -> HTTP 200
sh  FREE  qzxv93k7blorptun.sh   -> HTTP 404
co  TAKEN t.co (zone path)      -> HTTP 200
co  FREE  qzxv93k7blorptun.co   -> HTTP 404
us  TAKEN nic.us                -> HTTP 200
us  FREE  qzxv93k7blorptun.us   -> HTTP 404
so  TAKEN nic.so                -> HTTP 200
so  FREE  qzxv93k7blorptun.so   -> HTTP 404
de  TAKEN denic.de              -> HTTP 200
de  FREE  qzxv93k7blorptun.de   -> HTTP 404
```

## D5. Conflict preserved (per deep-research protocol)
- Main session: whois.registry.co answered correctly for nic.co (record) and qzxv93k7blorptun.co (DOMAIN NOT FOUND).
- Agent 1: whois.registry.co answered 'DOMAIN NOT FOUND' for t.co — a REGISTERED domain (false negative).
- Assessment: .co port-43 WHOIS is unreliable post-migration (Team Internet took over .co 2025-10-03); possibly query-format-sensitive or object-scoped. The .co RDAP endpoint (rdap.registry.co/co/) answered correctly for t.co in BOTH evidence classes. Design consequence: for .co, RDAP is the only trusted channel; never let WHOIS override RDAP.
