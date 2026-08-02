# Logo Builder

Home of logo projects made with the global `/acos-logo-forge` skill
(`~/.claude/skills/acos-logo-forge/`). One folder per business:

    <business-slug>/
      brief.md            interview answers
      fonts/              TTF/OTF outline sources (OFL or system)
      candidates/         generated rounds (round-1/, round-2/, ...), each with its own meta.json; all rounds stay visible
      commands.jsonl      browser -> Claude bridge
      projects/           saved editor documents
      exports/            final SVG/PNG (light + dark)

`_smoke/` is the build-verification workspace (2026-07-26) — a working example.
Launch any workspace with:

    bash ~/.claude/skills/acos-logo-forge/scripts/logoforge.sh "<workspace>" 8815
