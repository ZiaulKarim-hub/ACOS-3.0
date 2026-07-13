---
name: prism-financial-modeler
user-invocable: false
description: "Institutional-grade financial modeling and document production for private credit, PE, and alternative investments."
version: "1.0"
updated: "2026-01-19"
---

# PRISM Financial Modeler Engine

Institutional-grade financial modeling and document production for private credit, private equity, and alternative investments. **Fully integrated locally** with knowledge graph sync and YAML templates.

## Quick Start

```bash
# Create a new bridge loan model
prism bridge-loan "Deal Name" --borrower "Borrower LLC" --loan-amount 5000000

# Sync model to knowledge graph
prism sync deals/02_active/deal-name/model.xlsx

# Validate model
prism validate deals/02_active/deal-name/model.xlsx
```

## Triggers

Use this skill when:
- Creating Excel financial models (loan sizing, waterfalls, LBO, real estate, CLO)
- Generating investment committee memos
- Creating presentations for investors or IC
- Performing deal analysis requiring institutional standards
- Running due diligence document processing
- Generating credit memos or deal summaries

**Trigger phrases:** "financial model", "Excel model", "waterfall", "loan sizing", "IC memo", "credit memo", "deal analysis", "due diligence processing"

## Available Commands

| Action | Description |
|---------|-------------|
| `prism <template> "name"` | Create new model from template |
| `prism sync <path>` | Sync model to knowledge graph |
| `prism validate <path>` | Validate model for errors |
| `prism recalc <path>` | Recalculate formulas with LibreOffice |
| `prism templates` | List available templates |
| `sync-prism-model <path>` | Direct KG sync command |

## Available Templates

| Template | Description | OKOA Use Case |
|----------|-------------|---------------|
| `bridge-loan` | Short-term real estate bridge loan | Acquisition, refinance, renovation |
| `construction-loan` | Construction/development financing | Ground-up, heavy renovation |
| `preferred-equity` | Preferred equity investment | Mezzanine position |
| `lp-gp-waterfall` | LP/GP fund waterfall | Fund distributions |
| `real-estate-debt` | General real estate debt | Flexible debt structures |

## Capabilities

### Financial Modeling
- Private equity fund modeling (fees, carry, expense allocation)
- Real estate investment & debt (development pro formas, multi-property portfolios)
- Private credit & structured products (direct lending, CLO/CDO, ABS)
- Distribution waterfall calculations (European/American, catch-up, clawback)
- Portfolio analytics (PME, J-curve, attribution)

### Document Production
- Investment committee memos (9 required sections)
- Credit memos with full audit trails
- Deal summaries with risk matrices
- Financial models with 5+ worksheets

### Due Diligence Processing
- Document classification against 252-item DD framework
- Data extraction with 100% integrity validation
- Synthdoc generation (individual and master compilation)
- Deal association and checklist management

### Knowledge Graph Integration (NEW)

**Automatic entity extraction** from Excel models:
- **Parties:** Borrower, guarantor, lender
- **Properties:** Address, type, valuation
- **Loans:** Amount, rate, term, structure
- **Covenants:** LTV, DSCR, debt yield thresholds
- **Claims:** Financial metrics with Excel cell provenance

**Fuzzy matching (≥90%)** prevents duplicate entities:
```
Model: "CMB Infrastructure"
KG:    party:cmb-infrastructure
→ 95% match → REUSE existing node (no duplicate)
```

**New node types:**
- `COVENANT` - Financial covenants with thresholds
- `CLAIM` - Financial metrics with Excel cell references

## Quality Standards

- **Calculation tolerance:** 0.000001 (6 decimal places)
- **Source minimum:** 3 independent sources for verification
- **Data integrity:** 100% accuracy (zero tolerance for rounding/fabrication)
- **Evidence levels:** Verified (3+ sources), Probable (2 sources), Open (1 source)

## Wall Street Conventions

- Blue fonts for input cells
- Black fonts for formulas/calculations
- Red fonts for negative numbers
- No hard-coded numbers in formulas
- XNPV/XIRR for uneven cash flows
- Standard growth calculations: (New/Old)^(1/n)-1

## File Structure

```
.claude/skills/prism-financial-modeler/
├── SKILL.md                    # This file
├── prism-agent-config.yaml     # Detailed modeling intelligence (568 lines)
├── scripts/
│   ├── __init__.py
│   ├── institutional_model.py  # Excel generation (651 lines)
│   ├── recalc_v2.py            # LibreOffice recalculation (602 lines)
│   ├── model_validator.py      # Validation logic (621 lines)
│   └── evidence_bundle.py      # Audit trail generation (388 lines)
├── templates/
│   ├── bridge-loan.yaml        # Bridge loan template
│   └── (additional templates)
└── references/
    └── (sample models, documentation)
```

## Dependencies

**Required (all installed):**
- LibreOffice - Formula recalculation
- Python packages (via uv): openpyxl, reportlab, python-pptx
- Bun + exceljs - KG extraction

**Verify installation:**
```bash
libreoffice --version
~/.venv/bin/python3 -c "import openpyxl; print('✓ openpyxl')"
bun --version
```

## Integration

This skill integrates with:
- **Knowledge Graph:** `knowledge-graph/nodes.csv`, `knowledge-graph/edges.csv`
- **Managed Vault Refresh:** `knowledge-graph/scripts/rebuild_vault.py` refreshes `knowledge-graph/vault/` from the KG CSV artifacts
- **DD Framework:** `.system/dd-framework/` - DD processing pipeline
- **Agent Config:** `prism-agent-config.yaml` - Full agent specification

## Example Workflow

```bash
# 1. Create new deal folder
/okoa "new deal Kingston Duchesne"

# 2. Create PRISM model
prism bridge-loan "Kingston Duchesne" \
  --borrower "Michael Kingston" \
  --property "4270 W 5625 N, Roosevelt UT" \
  --loan-amount 6800000 \
  --interest-rate 12

# 3. Review and edit model in Excel
open deals/01_prospective/kingston-duchesne/model.xlsx

# 4. Sync to knowledge graph
prism sync deals/01_prospective/kingston-duchesne/model.xlsx

# 5. Run deal analysis (now includes KG data)
/okoa "analyze deal deals/01_prospective/kingston-duchesne/"

# 6. Generate DD checklist
/okoa "generate dd checklist kingston-duchesne"
```

## Architecture

**Prompt-first pattern** (proven in the canonical DD pipeline):

| Component | LOC | Purpose |
|-----------|-----|---------|
| `extract-prism-kg.ts` | ~80 | Pure I/O (read Excel → YAML) |
| `prism-to-kg-extraction.md` | ~300 | Intelligence (entity extraction, fuzzy matching) |
| Templates (YAML) | ~200 | Model structure definitions |
| Python scripts | ~2,262 | Excel generation, recalculation, validation |

**Why prompt-first:**
- Team can edit prompts (5 min) vs debug TypeScript (hours)
- Business logic in prompts is transparent and auditable
- Zero API cost (conversation mode execution)
- Proven: DD pipeline replaced 10,818 LOC with 2 prompts

---

*PRISM Financial Modeler - Locally integrated in okoa_ops*
*Last updated: 2026-01-13*
