# Hypercore Data Catalog

A complete, navigable map of **every value-bearing field Hypercore exposes** for loans, investors
(funding entities), borrowers (clients), and equities — each with the exact working path to fetch
it. Goal: answer any future portfolio question without reverse-engineering the schema each time
(the way the per-diem field had to be hunted down).

## Why this exists

The Hypercore GraphQL schema is large (599 types, 84 read resolvers) and the values you ask for are
often nested or in arrays (e.g. the per-diem lives at
`loanFundings…repaymentSchedule.scheduleTable[].due.interest`). A flat field list misses them, and a
schema path alone is useless without the *reliable* query that reaches it and the *real scale* of
the value (the percent-vs-fraction and net-vs-principal traps are invisible until you fetch a real
number). This catalog records all three: **logical name + path + working query + probed example +
gotchas.**

## Build pipeline (6 phases)

| Phase | What | Tool / output |
|------|------|---------------|
| 1 Harvest | Walk the 5 domain root types to bounded depth; emit every value-bearing leaf path, tiered active (current-state values) vs extended (drafts/history/config) | `hca-catalog-harvest.py` → `catalog-candidates.json` |
| 2 Classify | Per domain: logical name + synonyms, value-kind, reliable working query | workflow (per-domain agents) |
| 3 Probe | Compile paths → one GraphQL selection per value block, fetch a representative entity, map each path to a real value; pin scale/semantics | `hca-catalog-probe.py` |
| 4 Synthesize | Merge into `hypercore-catalog.yaml` (machine) + `HYPERCORE-FIELD-MAP.md` (human, by domain) | workflow synthesis |
| 5 Wire | Connect catalog to smart-ask routing; surface unwired-value backlog | `hca-ask.py` |
| 6 Maintain | Re-introspect + diff vs committed catalog → flag schema drift | `hca-catalog-refresh.py` |

## Domain roots & reliable access

| Domain | Root type | Reliable resolver |
|--------|-----------|-------------------|
| loan | `Loan` | `loans(filter:{searchString}){ pageItems{…} }` (+ `summary`) |
| investor | `LoanFunding` | `loanFundings` 2-step (`assetId` → `loanFundingId`) |
| funding_entity | `FundingEntity` | `fundingEntities(filter){ pageItems{…} }` |
| borrower | `Client` | `clients(filter){ pageItems{…} }` |
| equity | `Equity` | `equities(filter){ pageItems{…} }` |

Flaky (avoid): `loan(id)` and per-id resolvers intermittently HTTP 500 — always use the list+filter
path. `loanFundings` dual-filter (loanId+fundingEntityId together) 500s — use the 2-step.

## Tiering

`active` = current-state value blocks an analyst asks for (`summary`, `repaymentSchedule`,
`loanKPIs`, `agingAnalysis`, `mergedLoanFundingsSummary`, `receivables`, `cashReceived`, `terms`,
direct scalars). `extended` = drafts / `expected*`/`original*` schedule variants / transaction &
update history / audit / workflow / templates (recorded, not in the active catalog). Scale at
depth 4: ~5,200 active value-leaves across the five domains.

## Regenerate

```bash
# refresh the schema snapshot (live, read-only)
HCA_INTROSPECTION_OUT=.claude/skills/acos-hypercore-ask/catalog/_introspection_current.json \
  doppler run --project hypercore-ask --config dev_personal -- \
  python3 .claude/scripts/hca-introspect-full.py

# rebuild the candidate inventory
python3 .claude/skills/acos-hypercore-ask/catalog/hca-catalog-harvest.py --depth 4

# validate the probe mechanism (example)
doppler run --project hypercore-ask --config dev_personal -- \
  python3 .claude/skills/acos-hypercore-ask/catalog/hca-catalog-probe.py \
  --domain loan --prefix summary --name "Beehive" --limit 30
```

The two `*.json` artifacts are gitignored (large, regenerable). The committed catalog
(`hypercore-catalog.yaml` + `HYPERCORE-FIELD-MAP.md`) is the durable output.
