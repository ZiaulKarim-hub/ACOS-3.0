---
name: acos-electronics-repair
description: Interactive circuit board diagnostics and repair assistant. Indexes board components from photos, guides fault isolation through prioritized multimeter testing, and provides repair instructions.
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
---

# ACOS Electronics Repair

## Overview

An interactive, multi-phase electronics repair skill that turns Claude into a guided
diagnostic assistant. Upload circuit board photos, describe the problem, and get
walked through systematic fault isolation using your multimeter — step by step,
component by component, until the fault is found and fixed.

## Arguments

`$ARGUMENTS` may contain:
- `resume {session-id}` — Resume a previous diagnostic session
- `status` — List all diagnostic sessions
- A device description to start a new session (e.g., "Samsung TV power supply board won't turn on")

## Protocol

### Phase 0: Safety & Context

**This phase ALWAYS runs first. Safety is non-negotiable.**

#### Step 0.1: Parse Arguments

```
If $ARGUMENTS contains "status":
  → List sessions in .acos/sessions/electronics-repair/
  → Show: session-id, device, symptom, status, date
  → STOP

If $ARGUMENTS contains "resume":
  → Read the session manifest
  → Load board-index.yaml, diagnostic-log.yaml, differential.yaml
  → Display current state and resume from last phase
  → JUMP to the appropriate phase

Otherwise:
  → Start new session
```

#### Step 0.2: Create Session

```yaml
session_id: "er-{YYYYMMDD}-{HHMMSS}"
session_dir: ".acos/sessions/electronics-repair/{session_id}"
```

Create the session directory and initialize `session-manifest.yaml` from the template.

#### Step 0.3: Safety Assessment

Ask the user (use AskUserQuestion):

> **What type of device is this?**
> [1] Battery-powered (phone, laptop, toy, remote)
> [2] USB/low-voltage powered (Arduino, Raspberry Pi, LED strip)
> [3] Wall-powered (TV, monitor, router, charger, appliance)
> [4] Mains/high-voltage (power supply, inverter, UPS, industrial)
> [5] Vehicle/automotive (ECU, dashboard, charger)
> [6] Other (describe)

Based on the device type, display the appropriate **MANDATORY SAFETY WARNINGS**:

- **Types 3-4**: "WARNING: This device connects to mains power. Capacitors may hold LETHAL charge even when unplugged. BEFORE touching the board: discharge ALL large capacitors through a 10kΩ resistor. If you are unsure how to do this safely, DO NOT proceed without guidance."
- **Types 1-2**: "Ensure the device is powered off and batteries are removed."
- **Type 5**: "Disconnect the battery. Some automotive circuits remain live — check with multimeter before touching."
- **All types**: "Use an ESD wrist strap if available, especially when handling ICs or MOSFETs."

#### Step 0.4: Device History Interview

Ask the user:

1. **What is this device?** (Brand, model, what it does)
2. **What is the symptom?** Present options:
   - [A] Won't power on at all
   - [B] Powers on but doesn't work properly (describe)
   - [C] Intermittent / random failures
   - [D] Overheating
   - [E] Smoke, burning smell, or visible damage
   - [F] Strange noise (buzzing, whining, clicking)
   - [G] Other (describe)
3. **What happened before it stopped working?** (Power surge? Water? Drop? Just stopped? Gradual?)
4. **Do you have a schematic or service manual?** (Greatly helps if yes)
5. **What tools do you have?**
   - [a] Multimeter only
   - [b] Multimeter + soldering iron
   - [c] Multimeter + soldering iron + hot air station
   - [d] Full bench (oscilloscope, power supply, etc.)

Record all answers in `session-manifest.yaml`.

#### Step 0.5: Multimeter Verification

Ask the user to verify their multimeter works:

> "Quick check: set your multimeter to continuity mode and touch the two probes together. Does it beep? (This confirms your multimeter is working and your probes are connected.)"

### Phase 1: Board Indexing & Component Map

#### Step 1.1: Photo Upload

Ask the user to upload circuit board photos:

> "Please upload photos of the circuit board. Ideally:
> - **Top side** of the board (component side) — clear, well-lit, in focus
> - **Bottom side** (solder side) — if accessible
> - **Close-up of any damaged area** — if you can see damage
>
> Upload as many angles as helpful. Higher resolution = better component identification."

#### Step 1.2: Analyze & Index Components

For each uploaded photo, analyze and identify:

- **All major components**: ICs, capacitors (electrolytic, ceramic, film), resistors, MOSFETs/transistors,
  diodes, connectors, inductors, transformers, voltage regulators, fuses, crystals, relays, LEDs
- **Functional zones**: Power input, voltage regulation, logic/MCU, output stage, interface/connectors,
  protection circuits
- **Any visible damage**: Bulging caps, burn marks, cracked joints, corrosion, discoloration
- **Component markings**: Read part numbers, values, codes where visible

Assign each identified component a sequential number: `#1`, `#2`, `#3`, etc.

Create `board-index.yaml` with the full component table:

```yaml
components:
  - id: 1
    designator: "U1"          # If readable on board (silkscreen)
    type: "Voltage Regulator"
    description: "LM7805CT, TO-220 package"
    location: "Top-left, near DC input jack"
    zone: "Power"
    visual_status: "OK"        # OK, SUSPECT, DAMAGED
    notes: "Slight discoloration on PCB underneath"

  - id: 2
    type: "Electrolytic Capacitor"
    description: "470µF 25V, radial"
    location: "Adjacent to #1, left side"
    zone: "Power"
    visual_status: "SUSPECT"
    notes: "Top appears slightly bulged"
```

#### Step 1.3: Generate Component Map (SVG)

Generate an SVG diagram that serves as a visual reference map. The SVG should:

- Use a light background representing the board outline (approximate dimensions)
- Place **numbered circles** at each component's approximate position
- Color-code by zone: Red=Power, Blue=Logic, Green=Output, Orange=Interface, Gray=Other
- Color-code visual status: Yellow border=SUSPECT, Red border=DAMAGED
- Include a legend

Write the SVG to `{session_dir}/component-map.svg`.

**Tell the user**: "I've created a component map at `file://{absolute_path}/component-map.svg` — open it in your browser to see the numbered layout."

Also display the component table in text format so the user can reference it immediately.

#### Step 1.4: Identify Functional Blocks

Based on the component index, map out the functional block diagram:

```
Power Input → Protection → Voltage Regulation → Distribution
                                                      ↓
                              Output Stage ← Logic/MCU ← Clock
                                                      ↓
                                              Interface/IO
```

Write to `{session_dir}/block-diagram.yaml`.

### Phase 2: Visual Inspection (Guided)

#### Step 2.1: Systematic Visual Check

Walk the user through inspecting each component, prioritized by:
1. Components in the zone most likely related to the symptom
2. Components with known high failure rates (electrolytic caps first)
3. Components flagged as SUSPECT from photo analysis

For each component, ask specifically what to look for:

> "Look at **#2** (470µF electrolytic capacitor in the power section):
> - Is the top flat, or does it bulge upward?
> - Any brown or dark residue leaking from the top or bottom?
> - Is the plastic sleeve intact or cracked?
> What do you see?"

Update `board-index.yaml` with user observations. Update `visual_status` for each inspected component.

#### Step 2.2: Smell & Touch Check (if recently powered)

> "If you powered this device recently (last few minutes):
> - Can you smell any burnt or acrid odor from the board? Where is it strongest?
> - WITHOUT touching bare components, hover your hand ~1 inch above the board. Any area feel unusually warm?
> (Skip this if the device hasn't been powered recently.)"

#### Step 2.3: Visual Inspection Summary

Compile findings:
- Components confirmed DAMAGED
- Components flagged SUSPECT
- Components cleared as OK
- Any observations about solder joints, traces, or board condition

Write to `{session_dir}/visual-inspection.yaml`.

### Phase 3: Guided Diagnostic Loop

This is the **core interactive phase** — a loop that continues until the fault is isolated.

#### Step 3.1: Build Initial Differential List

Based on: symptom + device type + device history + visual inspection results + failure statistics.

Create `differential.yaml`:

```yaml
differential_list:
  - candidate_id: 1
    component: "#2 — 470µF electrolytic cap"
    hypothesis: "Dried out / high ESR, causing voltage rail ripple and MCU brownout"
    probability: "HIGH"
    supporting_evidence:
      - "Electrolytic cap, #1 failure component type"
      - "In power section, symptom is power-related"
      - "Visual: possibly bulging top"
    contradicting_evidence: []
    tests_to_confirm:
      - "Capacitance measurement"
      - "ESR measurement (if meter has ESR mode)"
      - "Visual confirmation of bulging"

  - candidate_id: 2
    component: "#5 — Main MOSFET"
    hypothesis: "Failed short, causing overcurrent / blown fuse"
    probability: "MEDIUM"
    ...
```

Display the differential list to the user:

> **Diagnostic Plan — Prioritized Suspects:**
> 1. 🔴 HIGH — **#2** (470µF cap): Likely dried out, causing power issues
> 2. 🟡 MEDIUM — **#5** (MOSFET): Possible short circuit
> 3. 🟡 MEDIUM — **#1** (Voltage regulator): May have failed
> 4. ⚪ LOW — **#8** (Fuse): Check if blown (and why)
>
> I'll guide you through testing each one, starting with the most likely. Ready?

#### Step 3.2: Test Loop

For each candidate (in priority order):

1. **Issue test instruction** — Specific, step-by-step:
   > "**Testing #2 (470µF electrolytic capacitor):**
   >
   > ⚠️ Make sure the board is powered OFF and unplugged.
   >
   > 1. Set your multimeter to **capacitance mode** (symbol: --||--)
   >    - If your meter doesn't have capacitance mode, set it to **resistance (200kΩ range)**
   > 2. Place the **red probe** on the **positive leg** (longer leg, or side WITHOUT the stripe marking)
   > 3. Place the **black probe** on the **negative leg** (shorter leg, or side WITH the stripe)
   >
   > **If using capacitance mode:** The reading should be close to 470µF (±20% is normal, so 376-564µF).
   > **If using resistance mode:** The value should start low and slowly climb toward OL as the cap charges.
   >
   > What does your multimeter show?"

2. **Receive and interpret reading**:
   - **Normal**: "Component #2 reads 445µF — that's within normal range. Marking as CLEARED. Moving to the next suspect."
   - **Abnormal**: "Component #2 reads 85µF — that's way below the 470µF rating. This cap has dried out. This is very likely your problem. But before we conclude, let me check one more thing..."
   - **Ambiguous**: "Reading is borderline. Let's try one more test to confirm..."

3. **Update differential list**:
   - Eliminate cleared candidates
   - Promote candidates consistent with findings
   - Add new candidates if a finding points to an unexpected direction

4. **Log to diagnostic-log.yaml**:
   ```yaml
   tests:
     - test_number: 1
       component_id: 2
       component: "470µF electrolytic cap"
       test_type: "Capacitance measurement"
       meter_mode: "Capacitance"
       expected: "376-564µF (470µF ±20%)"
       actual: "85µF"
       interpretation: "FAIL — capacitance 82% below rated value, capacitor has dried out"
       differential_update: "Candidate #1 promoted to CONFIRMED. Check for root cause (proximity to heat source)."
   ```

5. **Check for root cause chains**: If a fault is found, check if it could have been CAUSED by another fault:
   > "We found that #2 (capacitor) has dried out. But let's also check #5 (MOSFET) — sometimes a dried cap causes voltage spikes that kill the MOSFET. Set your multimeter to **diode mode**..."

6. **Loop** until:
   - Fault confirmed (one candidate clearly identified)
   - All high/medium candidates exhausted (suggest further investigation or professional repair)
   - User wants to stop

#### Step 3.3: Diagnosis Summary

When fault is isolated, present the diagnosis clearly:

> **DIAGNOSIS:**
> **Faulty component: #2** — 470µF 25V electrolytic capacitor (power filter)
>
> **What failed:** Capacitor has dried out (reads 85µF vs rated 470µF). This is a common age-related failure in electrolytic capacitors, especially near heat sources.
>
> **Why it caused your symptom:** This capacitor filters the main 5V power rail. With reduced capacitance, the rail has excessive ripple/noise, causing the microcontroller to brownout and the device to fail to power on.
>
> **Root cause:** Age + heat exposure (capacitor is adjacent to the voltage regulator which runs warm). The 85°C rated cap degraded faster due to proximity to heat.

### Phase 4: Repair Guidance

#### Step 4.1: Replacement Specification

> **Replacement part:**
> - **Type:** Electrolytic capacitor, radial lead
> - **Value:** 470µF
> - **Voltage:** 25V minimum (35V or 50V is OK — equal or higher)
> - **Temperature:** 105°C rated (upgrade from the original 85°C)
> - **Size:** ~10mm diameter × 16mm height (check it fits)
> - **Polarity:** YES — has positive and negative legs
>
> **Where to buy:**
> - Search "470µF 25V 105°C radial electrolytic capacitor" on Mouser, Digi-Key, or LCSC
> - Any reputable brand works: Nichicon, Panasonic, Rubycon, Wurth

#### Step 4.2: Replacement Procedure

Based on the user's available tools (from Phase 0):

**If user has soldering iron:**
> **Removal:**
> 1. Secure the board (use a PCB holder or tape to a flat surface)
> 2. Identify the cap's solder points on the bottom of the board
> 3. Heat one leg's solder pad with the iron tip (3-4 seconds)
> 4. Apply desoldering wick or use a solder sucker to remove solder
> 5. Repeat for the other leg
> 6. Gently pull the old capacitor free from the top side
>
> **Installation:**
> 1. **Check polarity!** Match the stripe (negative) side with the marking on the PCB
> 2. Insert the new capacitor's legs through the holes from the top side
> 3. Flip the board. Legs should poke through.
> 4. Apply solder to each leg — touch iron to pad+leg, feed solder, hold 2 seconds
> 5. Clip excess leg length with flush cutters
> 6. Inspect: joints should be shiny, concave, and wet both pad and leg

**If user has NO soldering iron:**
> "This repair requires soldering. You'll need at minimum:
> - A soldering iron (25-40W with fine tip)
> - Solder (0.8mm lead-free or 60/40 leaded)
> - Desoldering wick or solder sucker
> - Flush cutters
>
> Alternatively, a local electronics repair shop can do this swap for you — it's a simple repair."

#### Step 4.3: Post-Repair Validation

> **After replacing the component:**
>
> 1. **Visual check** — Inspect your solder joints. Are they shiny and smooth?
> 2. **Continuity check** — Test that the new component isn't shorted (set multimeter to resistance mode, measure across the capacitor — it should charge up, not stay at 0Ω)
> 3. **Power on test** — Plug in the device. Does it power on?
> 4. **Voltage rail check** — If you can access the board while powered:
>    measure the voltage rail near the replaced cap. Should read steady 5.0V (or whatever the rail voltage is).
> 5. **Full function test** — Test ALL device functions, not just the one that was broken
> 6. **Burn-in** — Let it run for 15-30 minutes. Check for excessive heat near the repair.

### Phase 4.5: Prevent Recurrence

> **Why this failed and how to prevent it:**
>
> The original 85°C rated capacitor was positioned directly adjacent to the voltage regulator,
> which generates heat. Electrolytic caps degrade faster at higher temperatures (lifetime halves
> for every 10°C above rated temperature).
>
> **Prevention:** By replacing with a 105°C rated capacitor, you've already improved the thermal
> margin by ~20°C, which roughly quadruples the expected lifetime. If this device allows it,
> you could also add a small heatsink to the voltage regulator to reduce ambient heat in that area.

Write the complete repair plan to `{session_dir}/repair-plan.yaml`.

### Session Completion

Update `session-manifest.yaml`:
```yaml
status: completed
diagnosis: "Dried electrolytic capacitor #2 (470µF) on 5V power rail"
components_replaced: ["#2"]
completion_date: "{timestamp}"
```

Display final summary with clickable file links to all session artifacts.

---

## Session State Management

All session data persists in `.acos/sessions/electronics-repair/{session-id}/`:

| File | Purpose |
|------|---------|
| `session-manifest.yaml` | Session metadata, device info, status |
| `board-index.yaml` | Numbered component map |
| `component-map.svg` | Visual SVG overlay with numbered markers |
| `block-diagram.yaml` | Functional block decomposition |
| `visual-inspection.yaml` | Visual inspection results |
| `differential.yaml` | Current differential diagnosis list |
| `diagnostic-log.yaml` | All test results and interpretations |
| `repair-plan.yaml` | Final diagnosis and repair instructions |

Sessions can be resumed at any phase via `$ARGUMENTS = "resume {session-id}"`.

---

## Agent Dispatch

This skill delegates to the `electronics-expert` agent for:
- Board photo analysis and component identification (Phase 1)
- SVG component map generation (Phase 1)
- Diagnostic reasoning and test selection (Phase 3)
- Repair specification and procedure (Phase 4)

The primary conversation handles:
- User interaction (questions, readings, confirmations)
- Session state management
- Safety gates

When spawning the electronics-expert agent, include:
- The session directory path
- All uploaded photos (via file paths)
- Current session state (manifest + any existing artifacts)
- The specific phase/step to execute

---

*ACOS Electronics Repair — Your guided circuit board diagnostics assistant.*
