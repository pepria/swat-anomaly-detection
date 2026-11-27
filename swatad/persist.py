"""Save and load the fitted state of a run (feature space and rule monitor) as JSON.

The state used to be pickled. Unpickling a file from somebody else can run arbitrary code, so the state
is plain JSON now and no pickle file is ever loaded. Pickles of an older run can be converted with
``scripts/convert_run_state.py`` (only do that for files you produced yourself).
"""
from __future__ import annotations

import json
from pathlib import Path

from .features import FeatureSpace
from .rules import RuleMonitor

NAME = "feature_space.json"


def save_run_state(run_dir: Path, fs: FeatureSpace, rules: RuleMonitor) -> Path:
    p = Path(run_dir) / NAME
    p.write_text(json.dumps({"fs": fs.to_dict(), "rules": rules.to_dict()}))
    return p


def load_run_state(run_dir: Path) -> tuple[FeatureSpace, RuleMonitor]:
    p = Path(run_dir) / NAME
    if not p.exists():
        old = Path(run_dir) / "feature_space.pkl"
        hint = (f" ({old.name} is an old pickle and is not loaded; convert one you trust with "
                "scripts/convert_run_state.py)") if old.exists() else ""
        raise FileNotFoundError(f"{p} not found{hint}")
    d = json.loads(p.read_text())
    return FeatureSpace.from_dict(d["fs"]), RuleMonitor.from_dict(d["rules"])
