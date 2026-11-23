"""Export per-anomaly JSON events from a finished run and explain them with the RAG layer.

    python scripts/export_and_explain.py [run_name] [model]
    (defaults: a12_A11-A10_noAIT GMM)

Writes
    outputs/anomalies/<run>__<model>.json        list of anomaly events (detector -> explainer interface)
    outputs/explanations/<run>__<model>.md        human-readable explanations
    outputs/explanations/<run>__<model>.json      structured explanations
    outputs/explanations/<run>__<model>_eval.csv  explanation quality per detected attack
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402
from swatad.events import EventExporter  # noqa: E402
from swatad.pipeline import make_setup, valid_mask  # noqa: E402
from swatad.rag.explainer import Explainer  # noqa: E402

run = sys.argv[1] if len(sys.argv) > 1 else "a12_A11-A10_noAIT"
model = sys.argv[2] if len(sys.argv) > 2 else "GMM"
C.ensure_dirs()
meta = json.loads((C.OUT_DIR / "runs" / run / "meta.json").read_text())
S = make_setup(meta["setup"], meta["train_sets"])
exp = EventExporter(C.OUT_DIR / "runs" / run, S.test, S.train[valid_mask(S.train)], S.events)
events = exp.export(model, use_rules=True)
name = f"{run}__{model}"
(C.OUT_DIR / "anomalies" / f"{name}.json").write_text(json.dumps(events, indent=1, default=str))
print(f"{len(events)} anomaly events")

E = Explainer()
_saved = C.OUT_DIR / "explanations" / f"{name}.json"
if os.environ.get("REUSE_EXPL") and _saved.exists():   # skip repeated LLM calls
    expl = json.loads(_saved.read_text())
    expl = [dict(x, markdown="") for x in expl]
    print("reusing saved explanations")
else:
    expl = [E.explain(ev) for ev in events]
md = [f"# Explanations: {run}, detector {model} (+rules)\n",
      f"Backend: {E.backend.name}. {len(events)} events. Ground-truth lines are added for evaluation "
      "only; the explainer never sees them.\n"]
md += [x["markdown"] for x in expl]
(C.OUT_DIR / "explanations" / f"{name}.md").write_text("\n".join(md))
(C.OUT_DIR / "explanations" / f"{name}.json").write_text(
    json.dumps([{k: v for k, v in x.items() if k != "markdown"} for x in expl], indent=1))


# ------------------------------------------------------------- explanation evaluation (A12 only)
def expand_targets(t: str) -> set:
    out = set()
    for part in re.split(r",\s*", t):
        m = re.match(r"([A-Z]+)(\d+)-(?:[A-Z]+)?(\d+)", part.strip())
        if m:
            a, b = int(m.group(2)), int(m.group(3))
            out |= {f"{m.group(1)}{i}" for i in range(a, b + 1)}
        else:
            out.add(part.strip())
    return out


GT_CAT = {"1": "actuator_manipulation", "2": "actuator_manipulation", "3": "standby_activation",
          "4": "spoof_out_of_range", "5": "actuator_manipulation", "6": "drift_or_inrange",
          "7": "standby_activation", "8": "standby_activation", "9": "spoof_out_of_range",
          "10": "oscillation", "11": "drift_or_inrange"}
if meta["setup"] == "a12":
    rows = []
    catalog = {c.title.split(":")[0].replace("A12 attack ", ""): c.chunk_id
               for c in E.retriever.chunks if c.source.startswith("04_")}
    E_loo = {aid: Explainer(backend="template", exclude_chunks=[cid]) for aid, cid in catalog.items()}
    seen = set()
    for ev, x in zip(events, expl):
        for g in ev.get("ground_truth_eval_only", []):
            aid = str(g["event_id"])
            if aid in seen:      # evaluate the first event that covers each attack
                continue
            # the event must start inside the attack (not a lingering earlier alarm)
            if pd.Timestamp(ev["start"]) < pd.Timestamp(g["start"]) - pd.Timedelta(seconds=10):
                continue
            seen.add(aid)
            targets = expand_targets(g["targets"])
            top3 = [t["tag"] for t in ev["top_contributors"][:3]]
            rule_tags = [r["tag"].split(".")[0] for r in ev["rule_hits"] if not r.get("already_active_before")]
            loo = E_loo[aid].explain(ev)
            loo_cat = [c for c in E_loo[aid].retriever.chunks if c.title in loo["similar_known_attacks"][:1]]
            loo_same = bool(loo_cat) and GT_CAT.get(loo_cat[0].title.split(":")[0].replace("A12 attack ", "")) == GT_CAT[aid]
            rows.append({
                "attack_id": aid, "event_id": ev["event_id"], "targets": g["targets"],
                "top3_contributors": ",".join(top3), "new_rule_tags": ",".join(rule_tags[:8]),
                "target_in_top3": bool(targets & set(top3)),
                "target_in_top3_or_rules": bool(targets & (set(top3) | set(rule_tags))),
                "predicted_category": x["category"], "true_category": GT_CAT[aid],
                "category_correct": x["category"] == GT_CAT[aid],
                "known_attack_top2": "; ".join(x["similar_known_attacks"]),
                "known_attack_correct": any(re.match(rf"A12 attack {aid}\b", s) for s in x["similar_known_attacks"][:2]),
                "loo_top1_same_category": loo_same,
            })
    ev_df = pd.DataFrame(rows).sort_values("attack_id", key=lambda s: s.astype(int))
    ev_df.to_csv(C.OUT_DIR / "explanations" / f"{name}_eval.csv", index=False)
    print(ev_df[["attack_id", "top3_contributors", "target_in_top3", "target_in_top3_or_rules",
                 "predicted_category", "category_correct", "known_attack_correct",
                 "loo_top1_same_category"]].to_string())
    print(ev_df[["target_in_top3", "target_in_top3_or_rules", "category_correct",
                 "known_attack_correct", "loo_top1_same_category"]].mean().round(2).to_string())
