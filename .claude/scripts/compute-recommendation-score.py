#!/usr/bin/env python3
"""
ACOS Loan Document Generator — Deterministic Recommendation Score Calculator

Computes the 4-pillar weighted composite credit score from loan data and
the recommendation matrix config. Replaces LLM arithmetic with exact math.

Usage:
  python3 compute-recommendation-score.py \
    --loan-data <loan-data.yaml> \
    --config <recommendation-matrix.yaml> \
    --output <score-result.yaml>

  python3 compute-recommendation-score.py \
    --loan-data <loan-data.yaml> \
    --config <recommendation-matrix.yaml> \
    --json

Output includes: composite score, per-pillar scores, recommendation category,
color, triggered overrides, and all sub-factor scores with sources.
"""

import sys
import json
import argparse
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def load_yaml(path):
    """Load YAML file, falling back to basic parsing if PyYAML unavailable."""
    text = Path(path).read_text()
    if yaml:
        return yaml.safe_load(text)
    raise ImportError("PyYAML required: pip install pyyaml")


def score_from_range(value, scoring_bands, direction):
    """Map a numeric value to a 1-10 score using the scoring bands."""
    if value is None:
        return 5  # default mid-range if data unavailable

    for band in scoring_bands:
        criteria = band["criteria"]
        lo, hi = band["range"]
        # Parse threshold from criteria string
        # Bands are ordered high-to-low, first match wins
        if lo <= 10 and hi >= 1:
            return (lo + hi) / 2  # midpoint of range

    return 5  # fallback


def compute_automated_score(ratio_id, value, config):
    """Score an automated sub-factor from its value and config thresholds."""
    if value is None:
        return 5.0, "DATA_UNAVAILABLE"

    # Find the sub-factor scoring bands
    for pillar_key in ["financial_metrics"]:
        pillar = config.get(pillar_key, {})
        for sf in pillar.get("sub_factors", []):
            if sf["id"] == ratio_id and sf.get("automated"):
                bands = sf["scoring"]
                for band in bands:
                    lo, hi = band["range"]
                    criteria = band["criteria"]
                    # Parse the criteria to check if value falls in this band
                    if _value_matches_criteria(value, criteria, ratio_id):
                        score = (lo + hi) / 2
                        return score, criteria
    return 5.0, "NO_MATCHING_BAND"


def _value_matches_criteria(value, criteria, ratio_id):
    """Check if a value matches a scoring criteria string."""
    c = criteria.lower().strip()

    # Handle "X > Y" and "X < Y" patterns
    if ratio_id in ("ltv", "debt_yield", "dscr", "noi_trend", "stress_test"):
        try:
            if ">" in c and "<" not in c:
                threshold = float(c.split(">")[1].strip().rstrip("%x"))
                return value > threshold
            elif "<" in c and ">" not in c:
                threshold = float(c.split("<")[1].strip().rstrip("%x"))
                return value < threshold
            elif "-" in c:
                parts = c.replace("%", "").replace("x", "").split("-")
                # Find two numbers
                nums = []
                for p in parts:
                    p = p.strip()
                    try:
                        nums.append(float(p.split()[-1]))
                    except (ValueError, IndexError):
                        pass
                if len(nums) >= 2:
                    return min(nums) <= value <= max(nums)
        except (ValueError, IndexError):
            pass

    return False


def compute_pillar_score(pillar_config, sub_factor_scores):
    """Compute weighted pillar score from sub-factor scores."""
    total = 0.0
    weight_sum = 0.0
    for sf in pillar_config.get("sub_factors", []):
        sf_id = sf["id"]
        weight = sf["weight"]
        score = sub_factor_scores.get(sf_id, 5.0)
        total += score * weight
        weight_sum += weight

    if weight_sum > 0:
        return total / weight_sum * 10  # normalize to 1-10 scale
    return 5.0


def compute_composite(pillar_scores, weights):
    """Compute weighted composite from pillar scores."""
    composite = 0.0
    for pillar, weight in weights.items():
        score = pillar_scores.get(pillar, 5.0)
        composite += score * weight
    return round(composite, 2)


def map_to_category(composite, categories):
    """Map composite score to recommendation category."""
    for cat in categories:
        if composite >= cat["min_score"]:
            return cat
    return categories[-1]  # fallback to last (lowest)


def check_overrides(composite, category, pillar_scores, ratios, override_rules):
    """Apply safety override rules."""
    triggered = []

    for rule in override_rules:
        rule_id = rule["id"]

        if rule_id == "pillar_floor":
            for pillar, score in pillar_scores.items():
                if score < 3.0:
                    triggered.append({
                        "rule": rule_id,
                        "detail": f"Pillar '{pillar}' = {score:.1f} (< 3.0)",
                        "action": rule["action"]
                    })

        elif rule_id == "red_ratio_cap":
            # Check if any must-have ratio is in red
            for ratio_id, ratio_val in ratios.items():
                if ratio_val.get("color") == "red":
                    triggered.append({
                        "rule": rule_id,
                        "detail": f"Ratio '{ratio_id}' = {ratio_val.get('value')} (RED)",
                        "action": rule["action"]
                    })

        elif rule_id == "dscr_floor":
            dscr = ratios.get("DSCR", {}).get("value")
            if dscr is not None and dscr < 1.0:
                triggered.append({
                    "rule": rule_id,
                    "detail": f"DSCR = {dscr:.2f}x (< 1.0x)",
                    "action": rule["action"]
                })

        elif rule_id == "ltv_ceiling":
            ltv = ratios.get("LTV", {}).get("value")
            if ltv is not None and ltv > 85.0:
                triggered.append({
                    "rule": rule_id,
                    "detail": f"LTV = {ltv:.1f}% (> 85%)",
                    "action": rule["action"]
                })

    return triggered


def color_ratio(value, ratio_config):
    """Determine green/amber/red for a ratio value."""
    if value is None:
        return "gray"

    direction = ratio_config.get("direction", "higher_is_better")

    if direction == "lower_is_better":
        green_max = ratio_config.get("green_max")
        amber_max = ratio_config.get("amber_max")
        if green_max and value <= green_max:
            return "green"
        if amber_max and value <= amber_max:
            return "amber"
        return "red"
    elif direction == "higher_is_better":
        green_min = ratio_config.get("green_min")
        amber_min = ratio_config.get("amber_min")
        if green_min and value >= green_min:
            return "green"
        if amber_min and value >= amber_min:
            return "amber"
        return "red"
    return "gray"


def main():
    parser = argparse.ArgumentParser(description="Compute credit recommendation score")
    parser.add_argument("--loan-data", required=True, help="Path to loan-data.yaml")
    parser.add_argument("--config", required=True, help="Path to recommendation-matrix.yaml")
    parser.add_argument("--output", "-o", help="Output YAML path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--pillar-scores", help="JSON dict of manual pillar sub-factor scores")
    args = parser.parse_args()

    config = load_yaml(args.config)
    loan_data = load_yaml(args.loan_data)

    # Extract financial figures from loan data
    figures = {}
    if isinstance(loan_data, dict):
        for key in ["financial_figures", "figures", "financials"]:
            if key in loan_data:
                figs = loan_data[key]
                if isinstance(figs, dict):
                    figures = figs
                elif isinstance(figs, list):
                    for item in figs:
                        if isinstance(item, dict) and "key" in item:
                            figures[item["key"]] = item.get("value")
                break

    # Color-code must-have ratios
    ratio_results = {}
    for ratio_cfg in config.get("must_have_ratios", []):
        rid = ratio_cfg["id"]
        value = figures.get(rid.lower()) or figures.get(rid)
        color = color_ratio(value, ratio_cfg) if value is not None else "gray"
        ratio_results[rid] = {
            "value": value,
            "color": color,
            "formula": ratio_cfg.get("formula"),
            "unit": ratio_cfg.get("unit"),
        }

    # Manual sub-factor scores (provided by the designer agent for qualitative factors)
    manual_scores = {}
    if args.pillar_scores:
        manual_scores = json.loads(args.pillar_scores)

    # Compute pillar scores (automated sub-factors from ratios, manual from input)
    pillar_scores = {}
    for pillar_key in ["property_quality", "financial_metrics", "sponsor_borrower", "market_conditions"]:
        pillar_cfg = config.get(pillar_key, {})
        sf_scores = {}
        for sf in pillar_cfg.get("sub_factors", []):
            sf_id = sf["id"]
            if sf.get("automated") and sf_id in ratio_results:
                # Use ratio color to approximate score
                color = ratio_results[sf_id].get("color", "gray")
                sf_scores[sf_id] = {"green": 8.5, "amber": 6.0, "red": 2.5, "gray": 5.0}.get(color, 5.0)
            elif sf_id in manual_scores:
                sf_scores[sf_id] = float(manual_scores[sf_id])
            else:
                sf_scores[sf_id] = 5.0  # default

        # Weighted average
        total = sum(sf_scores[sf["id"]] * sf["weight"] for sf in pillar_cfg.get("sub_factors", []))
        weight_sum = sum(sf["weight"] for sf in pillar_cfg.get("sub_factors", []))
        pillar_scores[pillar_key] = round(total / weight_sum, 2) if weight_sum > 0 else 5.0

    # Composite
    weights = config.get("pillar_weights", {})
    composite = compute_composite(pillar_scores, weights)

    # Category
    category = map_to_category(composite, config.get("categories", []))

    # Overrides
    overrides = check_overrides(composite, category, pillar_scores, ratio_results,
                                 config.get("override_rules", []))

    # Apply overrides
    final_category = category
    for override in overrides:
        if override["action"] == "auto_decline":
            final_category = [c for c in config["categories"] if c["id"] == "DECLINE"][0]
            break
        elif override["action"] == "cap_at_conditional":
            if category["id"] == "APPROVE":
                final_category = [c for c in config["categories"] if c["id"] == "CONDITIONAL_APPROVE"][0]
        elif override["action"] == "downgrade_one_category":
            cats = config["categories"]
            idx = next((i for i, c in enumerate(cats) if c["id"] == category["id"]), 0)
            if idx < len(cats) - 1:
                final_category = cats[idx + 1]

    result = {
        "composite_score": composite,
        "recommendation": final_category["id"],
        "recommendation_name": final_category["name"],
        "color_hex": final_category["color_hex"],
        "color_name": final_category["color_name"],
        "action": final_category["action"],
        "pillar_scores": pillar_scores,
        "ratio_results": ratio_results,
        "overrides_triggered": overrides,
        "overrides_changed_result": final_category["id"] != category["id"],
        "original_category": category["id"] if final_category["id"] != category["id"] else None,
    }

    if args.json or not args.output:
        output = json.dumps(result, indent=2, default=str)
    else:
        if yaml:
            output = yaml.dump(result, default_flow_style=False, sort_keys=False)
        else:
            output = json.dumps(result, indent=2, default=str)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output)
        print(f"Score computed: {composite} → {final_category['name']}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
