Resuming session via acos-eternity-protocol auto-resume.

CONTEXT HANDOFF: Read `memory/handoffs/2026-06-06-emergency-handoff.yaml` for full session state.

Quick summary:
- Working on: Built "Type-Forge" (standalone font-creation web app; skill renamed acos-font-forge -> acos-type-forge) and used it to FINALIZE a custom font "Xyntax Titles" (derivative of Cinzel Decorative, copyright Ziaul Karim).
- Last action: Exported the FINAL Xyntax Titles with 50 hand-tuned per-glyph spacing cushions baked in. Deliverables at "OKOA Website/font-foundry/xyntax/build/" (XyntaxTitles-Regular.ttf/.woff2 + FONTLOG + OFL). ri/re overlap slightly — USER ACCEPTED. Do NOT re-run the build unless asked.
- Next step: Font is DONE. Open item = Type-Forge home-page UPLOAD feature, BLOCKED awaiting user's answers to 3 design questions (see handoff): (1) multi-project switcher vs replace-active, (2) projects root location, (3) TTF-only-for-editing OK. Ask before building. Also optionally offered: wire font into a site via wire_astro.py.
- Blockers: Upload feature awaiting user's 3 answers. Type-Forge server may still run on port 8800 (specimen: http://127.0.0.1:8800/specimen.html?name=Xyntax%20Titles).

Key facts: skill is now acos-type-forge; editing assets/*.html needs relaunching scripts/typeforge.sh; localStorage prefix tf_; vectorize.py flags --space/--uc-space/--lc-space/--letter-space/--lc-scale/--spacing-file and strips inherited kerning; judge spacing by rendered ink (pixel-overlap), not the metric number.

This prompt was auto-injected after /clear ran. The user has not typed anything since. Read the handoff document and continue the prior work seamlessly.
