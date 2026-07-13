import os
import sys

SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from institutional_model import InstitutionalModel, create_institutional_model  # noqa: E402


def test_model_initializes_without_default_sheet_and_styles():
    model = InstitutionalModel("Test Model")
    assert model.wb.sheetnames == []

    style_names = {
        style.name if hasattr(style, "name") else style
        for style in model.wb.named_styles
    }
    assert "input" in style_names
    assert "formula" in style_names
    assert "link" in style_names
    assert "external" in style_names
    assert "header" in style_names
    assert "total" in style_names


def test_create_sheet_adds_sheet():
    model = InstitutionalModel("Test Model")
    ws = model.create_sheet("Assumptions")
    assert ws.title == "Assumptions"
    assert "Assumptions" in model.wb.sheetnames


def test_set_input_sets_style_and_ledger():
    model = InstitutionalModel("Test Model")
    ws = model.create_sheet("Assumptions")
    model.set_input(ws, "C4", 1000, model.CURRENCY, "source")

    cell = ws["C4"]
    assert cell.value == 1000
    assert cell.style == "input"
    assert cell.number_format == model.CURRENCY

    ledger = model.get_ledger()
    assert ledger[-1]["cell_type"] == "INPUT"
    assert ledger[-1]["cell"] == "C4"


def test_set_formula_requires_equals_prefix():
    model = InstitutionalModel("Test Model")
    ws = model.create_sheet("Calc")

    try:
        model.set_formula(ws, "C5", "C4*1.1")
    except ValueError as exc:
        assert "must start with '='" in str(exc)
    else:
        raise AssertionError("Expected ValueError for formula without '='")


def test_set_link_requires_sheet_reference():
    model = InstitutionalModel("Test Model")
    ws = model.create_sheet("Calc")

    try:
        model.set_link(ws, "B2", "=C4")
    except ValueError as exc:
        assert "must contain '!'" in str(exc)
    else:
        raise AssertionError("Expected ValueError for link without sheet reference")


def test_set_external_requires_bracket_reference():
    model = InstitutionalModel("Test Model")
    ws = model.create_sheet("Calc")

    try:
        model.set_external(ws, "B2", "=OtherSheet!C4")
    except ValueError as exc:
        assert "must contain '['" in str(exc)
    else:
        raise AssertionError("Expected ValueError for external link without '['")


def test_add_named_range_sanitizes_name():
    model = InstitutionalModel("Test Model")
    model.create_sheet("Assumptions")

    model.add_named_range("Total Revenue", "Assumptions", "C4")
    assert "Total_Revenue" in model.named_ranges
    assert model.named_ranges["Total_Revenue"] == "'Assumptions'!$C4"


def test_add_balance_check_adds_rules_and_ledger():
    model = InstitutionalModel("Test Model")
    ws = model.create_sheet("Checks")
    model.add_balance_check(ws, "C4", "=1-1", "Test check")

    rules_by_range = ws.conditional_formatting._cf_rules
    assert len(rules_by_range) == 1
    cf_range = next(iter(rules_by_range.keys()))
    assert "C4" in str(cf_range.sqref)
    rules = rules_by_range[cf_range]
    assert len(rules) == 2

    desc_cell = ws["D4"]
    assert desc_cell.value == "Test check"

    ledger = model.get_ledger()
    assert ledger[-1]["cell_type"] == "CHECK"


def test_create_institutional_model_helper():
    model = create_institutional_model("Helper Model")
    assert isinstance(model, InstitutionalModel)
    assert model.title == "Helper Model"
