"""Evaluate detection events and their explanations on SWaT 2015 (36 real attacks).

Needs a finished run of the 2015 setup (scripts/run_experiments.py s2015, or
swatad.pipeline.run("s2015", tag=...)) and the attack list turned into
knowledge_base/04_swat2015_attack_catalog.md plus the original List_of_attacks_Final.xlsx
(for the attack times).

    python scripts/eval_2015_explain.py <run tag> <List_of_attacks_Final.xlsx> [models, comma separated]

For every listed attack the first alarm event that starts in [start, end + 5 min] is explained
(template backend) and checked against the list: attacked tag in the top 3 contributors (or new
rule violations), category, retrieved attack, leave-one-out retrieval and confidence.
"""
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import openpyxl  # noqa: E402
import pandas as pd  # noqa: E402

from swatad import config as C  # noqa: E402
from swatad.events import EventExporter  # noqa: E402
from swatad.pipeline import make_setup, valid_mask  # noqa: E402
from swatad.rag.explainer import Explainer  # noqa: E402

CAT = "04_swat2015_attack_catalog.md"
run_tag, xlsx = sys.argv[1], Path(sys.argv[2])
MODELS = (sys.argv[3] if len(sys.argv) > 3 else "IForest,WinAE").split(",")
TOL = pd.Timedelta(seconds=C.EVENT_TOLERANCE_S)

# categories (catalog wording) -> signature categories that count as a reasonable reading
ACCEPT = {
    "actuator manipulation": {"actuator_manipulation", "standby_activation"},
    "standby equipment activation": {"standby_activation", "actuator_manipulation"},
    "sensor spoofing out of range": {"spoof_out_of_range", "out_of_range_excursion", "oscillation"},
    "sensor spoofing in range": {"drift_or_inrange", "out_of_range_excursion", "multivariate"},
}

# --- attack list with times ---------------------------------------------------------------------
rows = list(openpyxl.load_workbook(xlsx, read_only=True, data_only=True).active.iter_rows(values_only=True))[1:]
attacks = {}
for r in rows:
    if r[0] and str(r[0]).strip().isdigit() and r[4]:
        t0 = datetime.fromisoformat(str(r[1]))
        if t0 < datetime(2015, 12, 27):          # attacks 37-41 are listed as 2015-01-02 (typo for 2016)
            t0 = t0.replace(year=2016)
        h, m, s = (int(x) for x in str(r[2]).split(":"))
        t1 = t0.replace(hour=h, minute=m, second=s)
        if t1 < t0:
            t1 += timedelta(days=1)
        attacks[str(r[0]).strip()] = (pd.Timestamp(t0), pd.Timestamp(t1))

# --- catalog: targets and categories ------------------------------------------------------------
E0 = Explainer(backend="template", own_catalog=CAT)
cat_info = {}
for c in E0.retriever.chunks:
    if c.source == CAT:
        aid = re.match(r"SWaT2015 attack (\d+):", c.title).group(1)
        cat_info[aid] = {"chunk": c.chunk_id, "title": c.title,
                         "targets": re.search(r"Targets: ([^.]*)\.", c.text).group(1).split(", "),
                         "category": re.search(r"Category: ([^.]*)\.", c.text).group(1)}
by_title = {v["title"]: v["category"] for v in cat_info.values()}

S = make_setup("s2015")
test = S.test
gt = pd.DataFrame([{"event_id": a, "name": cat_info[a]["title"], "targets": ",".join(cat_info[a]["targets"]),
                    "start": attacks[a][0], "end": attacks[a][1], "type": cat_info[a]["category"],
                    "tag": cat_info[a]["targets"][0]} for a in attacks])
y = test["_label"].values
inside = [int(y[(test.index >= s) & (test.index <= e)].mean() * 100) for s, e in zip(gt.start, gt.end)]
print(f"alignment: {sum(v > 50 for v in inside)} of {len(gt)} listed attacks have > 50% of their listed "
      f"interval labelled as attack in the data (median {int(np.median(inside))}%)")

run_dir = C.OUT_DIR / "runs" / run_tag
train_v = S.train[valid_mask(S.train)]
exp = EventExporter(run_dir, test, train_v, gt)
E = Explainer(backend="template", own_catalog=CAT)

res = []
for model in MODELS:
    events = exp.export(model, use_rules=True)
    used = set()
    for ev in events:
        ex = E.explain(ev)
        t0 = pd.Timestamp(ev["start"])
        top = [t["tag"] for t in ev["top_contributors"]]
        new_rules = [h["tag"].split(".")[0] for h in ev["rule_hits"] if not h.get("already_active_before")]
        hit = [a for a in attacks if attacks[a][0] <= t0 <= attacks[a][1] + TOL and a not in used]
        base = {"model": model, "event_id": ev["event_id"], "start": ev["start"], "confidence": ex["confidence"],
                "confidence_raw": ex["confidence_raw"], "category_pred": ex["category"]}
        if not hit:
            res.append({**base, "kind": "false_alarm"})
            continue
        for a in hit:                                  # one event can start inside two adjacent attacks
            used.add(a)
            info = cat_info[a]
            tg = [t.replace("-", "") for t in info["targets"]]
            loo = Explainer(backend="template", exclude_chunks=[info["chunk"]], own_catalog=CAT).explain(ev)
            res.append({**base, "kind": "attack", "attack_id": a, "category_true": info["category"],
                        "tag_top3": any(t in top[:3] for t in tg),
                        "tag_top3_or_rules": any(t in top[:3] or t in new_rules for t in tg),
                        "category_ok": (ex["category"] in ACCEPT[info["category"]]) if info["category"] in ACCEPT else np.nan,
                        "known_top2": any(re.match(rf"SWaT2015 attack {a}\b", s) for s in ex["similar_known_attacks"][:2]),
                        "loo_same_category": by_title.get(loo["similar_known_attacks"][0]) == info["category"]})
    for a in attacks:
        if a not in used:
            res.append({"model": model, "kind": "missed", "attack_id": a, "category_true": cat_info[a]["category"]})

out = C.OUT_DIR / "s2015_explain"
out.mkdir(exist_ok=True)
df = pd.DataFrame(res)
df.to_csv(out / "detail.csv", index=False)
atk = df[df.kind.isin(["attack", "missed"])].copy()
atk["detected"] = (atk.kind == "attack")
print("\n== explanation quality on detected attacks ==")
for model, g in atk.groupby("model"):
    d = g[g.detected]
    f = lambda c: round(float(d[c].astype(float).mean()), 2)          # noqa: E731
    print(f"{model}: attacks {len(g)}, detected {len(d)} ({len(d) / len(g):.2f}); tag_top3 {f('tag_top3')}, "
          f"tag_top3_or_rules {f('tag_top3_or_rules')}, category_ok {f('category_ok')} "
          f"(n={int(d.category_ok.notna().sum())}), known_top2 {f('known_top2')}, loo_same_category {f('loo_same_category')}")
print("\n== by true category (detected only) ==")
print(atk[atk.detected].groupby(["model", "category_true"]).agg(
    n=("attack_id", "size"), tag_top3_or_rules=("tag_top3_or_rules", "mean"), category_ok=("category_ok", "mean"),
    known_top2=("known_top2", "mean")).round(2).to_string())
ev = df[df.kind.isin(["attack", "false_alarm"])].copy()
ev["ok"] = ev.tag_top3_or_rules.fillna(False).astype(bool)
print("\n== confidence: events, attack events, false-alarm events, share with the attacked tag found ==")
for col in ("confidence_raw", "confidence"):
    t = ev.groupby(["model", col]).agg(events=("kind", "size"), attack=("kind", lambda x: (x == "attack").sum()),
                                       false_alarm=("kind", lambda x: (x == "false_alarm").sum()), ok=("ok", "mean"))
    print(f"\n-- {col}\n{t.round(2).to_string()}")
