"""The explanation layer runs on the stored anomaly-event JSON (no SWaT data needed)."""
import copy
import json
from pathlib import Path

import pytest

from swatad.rag.explainer import CATEGORIES, Explainer, classify

ROOT = Path(__file__).resolve().parents[1]
EVENTS = json.loads((ROOT / "outputs/anomalies/a12_A11-A10_noAIT__WinAE.json").read_text())


@pytest.fixture(scope="module")
def explainer():
    return Explainer(backend="template")


def test_events_follow_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((ROOT / "docs/anomaly_event.schema.json").read_text())
    for ev in EVENTS:
        jsonschema.validate(ev, schema)


def test_classify_returns_known_category():
    for ev in EVENTS:
        cat, reasons = classify(ev)
        assert cat in CATEGORIES and isinstance(reasons, list)


def test_template_explanation_for_every_event(explainer):
    for ev in EVENTS:
        ex = explainer.explain(ev)
        assert ex["event_id"] == ev["event_id"] and ex["backend"] == "template"
        assert ex["markdown"].strip()


def test_ground_truth_does_not_leak(explainer):
    ev = copy.deepcopy(EVENTS[0])
    with_gt = explainer.explain(ev)
    ev.pop("ground_truth_eval_only", None)
    without_gt = explainer.explain(ev)
    keys = [k for k in with_gt if k != "markdown"]
    assert {k: with_gt[k] for k in keys} == {k: without_gt[k] for k in keys}
