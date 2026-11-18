"""Explanation layer: anomaly-event JSON -> retrieval -> explanation.

Two back-ends share the same retrieval step:

* ``TemplateBackend`` (default, offline): rule-based signature classification +
  retrieved knowledge -> structured explanation and a Markdown report.
* ``ClaudeBackend`` (hook): sends the event JSON and the retrieved chunks to the
  Claude API and asks for the same structured explanation. Used only when the
  ``anthropic`` package is installed and an API key is configured.

    from swatad.rag.explainer import Explainer
    exp = Explainer()                    # or Explainer(backend="claude")
    result = exp.explain(event_json)     # dict
    print(result["markdown"])
"""
from __future__ import annotations

import json
import os

from .retriever import Retriever
from .tags import STAGE_NAMES

# signature -> (human label, query words used to retrieve the matching pattern chunk)
CATEGORIES = {
    "standby_activation": ("activation of standby or unused equipment",
                           "standby unused equipment pump valve never changes activation"),
    "spoof_out_of_range": ("sensor value forced outside its normal range (spoofing or stuck sensor)",
                           "sensor spoofing out-of-range constant value flat stuck frozen"),
    "oscillation": ("oscillating / multi-value sensor values (spoofing or noise)",
                    "oscillating multi-value spoofing jumps variance noise"),
    "actuator_manipulation": ("illegal combination of actuator states (actuator manipulation)",
                              "actuator manipulation illegal valve pump combination"),
    "out_of_range_excursion": ("process variable outside its normal range",
                               "out-of-range process value overflow level excursion"),
    "drift_or_inrange": ("gradual drift or in-range deviation (drift fault or in-range spoofing)",
                         "drift in-range spoofing rate of change slow deviation"),
    "multivariate": ("broken relation between correlated sensors",
                     "relation between sensors broken replay correlation invariant"),
}

CHECKS = {
    "standby_activation": ["Check the HMI/PLC command log for who switched the equipment and whether "
                           "maintenance was scheduled.",
                           "Verify physically that the standby unit is running.",
                           "If it is a dosing pump, check chemical concentrations immediately (AIT201-203)."],
    "spoof_out_of_range": ["Compare the reading with physically related tags (flows, connected tank "
                           "levels, pump states).",
                           "Inspect the transmitter locally and check PLC register writes.",
                           "Put the affected control loop in manual if the value drives an actuator."],
    "oscillation": ["Check whether the rate of change is physically possible for the tank/process.",
                    "Inspect wiring, grounding and PLC tag writes."],
    "actuator_manipulation": ["Compare commanded and actual valve/pump positions.",
                              "Check the PLC mode (auto/manual) and recent operator commands.",
                              "Check downstream flows and levels for the expected reaction."],
    "out_of_range_excursion": ["Check whether a real process excursion is happening (overflow, "
                               "pressure).",
                               "Check the actuators that control this variable."],
    "drift_or_inrange": ["Check the instrument calibration and compare with a reference measurement.",
                         "Check the mass balance between inflow, outflow and level."],
    "multivariate": ["Check the physical invariants of the stage (actuator state vs flow).",
                     "Consider a replay attack if values look normal but disagree with actuators."],
}


def classify(ev: dict) -> tuple[str, list[str]]:
    """Heuristic signature of the event; returns (category, reasons)."""
    top = ev["top_contributors"]
    new_rules = [r for r in ev.get("rule_hits", []) if not r.get("already_active_before")]
    reasons = []
    unseen = [r for r in new_rules if r["rule"] == "unseen_state" and r["kind"] == "actuator"]
    def _is_pump(r):
        t = r["tag"].split(".")[0]
        return t.startswith("P") and not t.startswith("PIT")
    standby = [r for r in unseen if _is_pump(r) and r.get("normal_values") == [1.0]
               and 2.0 in r.get("observed_values", [])]
    if standby:
        reasons.append("normally-off pump(s) switched on: " + ", ".join(r["tag"].split(".")[0] for r in standby))
        return "standby_activation", reasons
    if len(unseen) >= 2:
        reasons.append("several actuators took states never seen in normal operation: "
                       + ", ".join(r["tag"].split(".")[0] for r in unseen[:6]))
        return "actuator_manipulation", reasons
    oor = [r for r in new_rules if r["rule"] == "out_of_range"]
    sens = [t for t in top[:3] if t["kind"] == "sensor"]
    for t in oor + sens:
        sig = t.get("signal", {})
        if sig.get("direction_changes_per_min", 0) > 10 and sig.get("max_step_sigma", 0) > 1:
            name = t["tag"].split(".")[0]
            reasons.append(f"{name} jumps back and forth ({sig['direction_changes_per_min']} direction "
                           f"changes/min, steps up to {sig['max_step_sigma']} sigma)")
            return "oscillation", reasons
    for r in oor:
        if r.get("signal", {}).get("flat_fraction", 0) > 0.6:
            reasons.append(f"{r['tag'].split('.')[0]} outside normal range and flat "
                           f"({r['signal']['flat_fraction']:.0%} of steps unchanged)")
            return "spoof_out_of_range", reasons
    acts = [t for t in top[:3] if t["kind"] == "actuator"]
    if len(acts) >= 2 or (acts and top[0]["kind"] == "actuator"):
        reasons.append("top contributors are actuators: " + ", ".join(t["tag"] for t in acts))
        return "actuator_manipulation", reasons
    if oor:
        reasons.append("out of range: " + ", ".join(r["tag"].split(".")[0] for r in oor))
        return "out_of_range_excursion", reasons
    if len(unseen) == 1:
        reasons.append(f"normally constant actuator {unseen[0]['tag'].split('.')[0]} changed state")
        return "standby_activation", reasons
    for t in sens:
        sig = t.get("signal", {})
        if sig.get("flat_fraction", 0) > 0.9:
            reasons.append(f"{t['tag']} frozen ({sig['flat_fraction']:.0%} of steps unchanged)")
            return "spoof_out_of_range", reasons
        if abs(sig.get("slope_per_min", 0)) > 0 and t.get("direction") in ("high", "low"):
            reasons.append(f"{t['tag']} trending {t['direction']}")
            return "drift_or_inrange", reasons
    reasons.append("no single dominant tag; several sensors deviate together")
    return "multivariate", reasons


def build_query(ev: dict, category: str) -> tuple[str, list[str]]:
    tags = [t["tag"] for t in ev["top_contributors"][:3]]
    tags += [r["tag"].split(".")[0] for r in ev.get("rule_hits", []) if not r.get("already_active_before")]
    tags = list(dict.fromkeys(tags))
    words = [CATEGORIES[category][1]]
    for t in ev["top_contributors"][:3]:
        words.append(f"{t['tag']} {t['description']} {t.get('direction', '')}")
    for st in ev["stages_involved"]:
        words.append(f"stage {st} {STAGE_NAMES.get(st, '')}")
    return " ".join(words), tags


def _fmt_tag(t: dict) -> str:
    if t["kind"] in ("actuator", "alarm", "state"):
        return (f"{t['tag']} ({t['description']}): values {t.get('values_in_event')} "
                f"(normal {t.get('normal_values')})")
    return (f"{t['tag']} ({t['description']}): {t['value_min']:.4g} to {t['value_max']:.4g} {t['unit']} "
            f"vs normal {t['normal_p01']:.4g} to {t['normal_p99']:.4g} -> {t['direction']}")


class TemplateBackend:
    name = "template"

    def generate(self, ev, category, reasons, retrieved):
        label = CATEGORIES[category][0]
        top = ev["top_contributors"]
        known = [(c, s) for c, s in retrieved if c.source.startswith("04_")]
        patterns = [(c, s) for c, s in retrieved if c.source.startswith("03_")]
        process = [(c, s) for c, s in retrieved if c.source.startswith("01_")]
        inv = [(c, s) for c, s in retrieved if c.source.startswith("05_")]
        stages = ", ".join(f"{s} ({STAGE_NAMES.get(s, '?')})" for s in ev["stages_involved"]) or "-"
        summary = (f"Between {ev['start'][11:19]} and {ev['end'][11:19]} ({ev['duration_s']} s) the "
                   f"{ev['model']} detector{' and the rule layer' if ev['rule_hits'] else ''} flagged an "
                   f"anomaly in {stages}; peak score {ev['max_score_ratio']:.1f}x the threshold. "
                   f"Most likely interpretation: {label}.")
        evidence = [_fmt_tag(t) for t in top[:3]]
        new_hits = [r for r in ev["rule_hits"] if not r.get("already_active_before")]
        for r in new_hits[:6]:
            if r["rule"] == "unseen_state":
                evidence.append(f"Rule: {r['tag'].split('.')[0]} took value(s) {r['observed_values']} "
                                f"never seen in normal operation (normal {r['normal_values']}).")
            else:
                evidence.append(f"Rule: {r['tag'].split('.')[0]} left its normal range "
                                f"{r['normal_range']} (observed {r['observed_min']} to {r['observed_max']}).")
        if len(new_hits) > 6:
            evidence.append(f"... and {len(new_hits) - 6} more rule violations: "
                            + ", ".join(r["tag"].split(".")[0] for r in new_hits[6:]))
        out = {
            "summary": summary,
            "category": category,
            "category_label": label,
            "reasons": reasons,
            "evidence": evidence,
            "similar_known_attacks": [c.title for c, _ in known[:2]],
            "pattern": patterns[0][0].title if patterns else None,
            "process_context": [c.text.split("\n", 1)[1][:400] for c, _ in process[:1]],
            "relevant_invariants": [c.text.split("\n", 1)[1] for c, _ in inv[:2]],
            "recommended_checks": CHECKS[category],
            "confidence": "high" if ev["rule_hits"] and ev["max_score_ratio"] > 2 else
                          "medium" if ev["max_score_ratio"] > 1.5 or ev["rule_hits"] else "low",
            "sources": [c.chunk_id for c, _ in retrieved],
        }
        return out


class ClaudeBackend:
    """LLM hook. Needs `pip install anthropic` and an API key (ANTHROPIC_API_KEY or `ant auth login`)."""
    name = "claude"
    SYSTEM = (
        "You explain anomalies detected in the SWaT water treatment testbed to a plant operator. "
        "You get one anomaly event (JSON produced by the detector) and excerpts from a knowledge "
        "base. Base every statement on the event data or the excerpts, cite excerpt ids in square "
        "brackets, and say clearly when the evidence is weak. Answer with a JSON object with keys: "
        "summary (2-3 sentences), category_label, evidence (list of strings), "
        "similar_known_attacks (list), recommended_checks (list), confidence (low/medium/high)."
    )

    def __init__(self, model: str = "claude-opus-5-5"):
        import anthropic  # imported lazily so the package stays optional
        self.client = anthropic.Anthropic()
        self.model = model

    def generate(self, ev, category, reasons, retrieved):
        ctx = "\n\n".join(f"[{c.chunk_id}] {c.text}" for c, _ in retrieved)
        prompt = (f"Anomaly event:\n```json\n{json.dumps(ev, indent=1)}\n```\n\n"
                  f"Rule-based pre-classification: {category} ({'; '.join(reasons)})\n\n"
                  f"Knowledge base excerpts:\n{ctx}")
        resp = self.client.beta.messages.create(
            model=self.model, max_tokens=16000,
            thinking={"type": "adaptive"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default",
            system=self.SYSTEM, messages=[{"role": "user", "content": prompt}])
        if resp.stop_reason == "refusal":
            raise RuntimeError("the model declined to answer")
        text = "".join(b.text for b in resp.content if b.type == "text")
        try:
            out = json.loads(text[text.index("{"): text.rindex("}") + 1])
        except ValueError:
            out = {"summary": text}
        out.update(category=category, sources=[c.chunk_id for c, _ in retrieved])
        return out


def to_markdown(ev: dict, ex: dict) -> str:
    lines = [f"### {ev['event_id']}  ({ev['start'][11:19]} - {ev['end'][11:19]})", "",
             ex["summary"], "", "**Evidence**"]
    lines += [f"- {e}" for e in ex.get("evidence", [])]
    if ex.get("similar_known_attacks"):
        lines += ["", "**Similar known attacks:** " + "; ".join(ex["similar_known_attacks"])]
    if ex.get("pattern"):
        lines += [f"**Matching pattern:** {ex['pattern']}"]
    if ex.get("relevant_invariants"):
        lines += ["", "**Relevant physical rules**"] + [f"- {i}" for i in ex["relevant_invariants"]]
    lines += ["", "**Recommended checks**"] + [f"- {c}" for c in ex.get("recommended_checks", [])]
    lines += ["", f"Confidence: {ex.get('confidence')}. Sources: {', '.join(ex.get('sources', []))}"]
    gt = ev.get("ground_truth_eval_only")
    if gt is not None:
        g = "; ".join(f"#{x.get('event_id')} {x.get('name', x.get('type', ''))}" for x in gt) or "none (false alarm)"
        lines += [f"_Ground truth (evaluation only, not given to the explainer): {g}_"]
    return "\n".join(lines) + "\n"


class Explainer:
    def __init__(self, backend: str = "auto", exclude_chunks=()):
        self.retriever = Retriever()
        self.exclude = set(exclude_chunks)   # e.g. leave-one-out evaluation of the catalog
        if backend == "auto":
            backend = "claude" if os.environ.get("ANTHROPIC_API_KEY") and _has_anthropic() else "template"
        self.backend = ClaudeBackend() if backend == "claude" else TemplateBackend()

    def retrieve(self, query: str, tags: list[str], category: str):
        """Multi-source retrieval: a fixed budget per document type, so that tag
        definitions do not crowd out attack knowledge."""
        R, ex = self.retriever, self.exclude
        got = []

        def add(items):
            for c, sc in items:
                if c.chunk_id not in ex and c.chunk_id not in {x.chunk_id for x, _ in got}:
                    got.append((c, sc))
        # 1) dictionary entries of the implicated tags (exact lookup)
        for t in tags[:4]:
            add([(c, 1.0) for c in R.chunks if c.source.startswith("02_") and c.title.startswith(t + " ")])
        # 2) generic attack / fault pattern matching the signature
        add(R.search(CATEGORIES[category][1] + " " + query, tags, k=2 + len(ex),
                     sources=["03_attack_and_fault_patterns.md"])[:1])
        # 3) known incidents, 4) physical invariants, 5) process description
        add([x for x in R.search(query, tags, k=2 + len(ex), sources=["04_a12_attack_catalog.md"])
             if x[0].chunk_id not in ex][:2])
        add([x for x in R.search(query, tags, k=2, sources=["05_mined_invariants.md"]) if x[1] > 0.05][:2])
        add(R.search(query, tags, k=1, sources=["01_process_overview.md"]))
        return got

    def explain(self, ev: dict) -> dict:
        # never leak ground truth into the explanation
        ev_in = {k: v for k, v in ev.items() if k != "ground_truth_eval_only"}
        category, reasons = classify(ev_in)
        query, tags = build_query(ev_in, category)
        retrieved = self.retrieve(query, tags, category)
        ex = self.backend.generate(ev_in, category, reasons, retrieved)
        ex["event_id"] = ev["event_id"]
        ex["backend"] = self.backend.name
        ex["markdown"] = to_markdown(ev, ex)
        return ex


def _has_anthropic() -> bool:
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False
