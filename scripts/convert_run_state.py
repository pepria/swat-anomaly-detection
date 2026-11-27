"""Convert the pickled run state of an older run to JSON (swatad.persist).

    python scripts/convert_run_state.py outputs/runs/<run>   [...]

**Only convert pickles that you produced yourself.** Unpickling runs the code stored in the file; this is the
reason the state is JSON now. The pickle is read once here, written as feature_space.json, and left in place.
"""
import pickle
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from swatad.persist import save_run_state  # noqa: E402

for d in sys.argv[1:]:
    with open(Path(d) / "feature_space.pkl", "rb") as f:        # trusted, self-made file
        obj = pickle.load(f)
    print("written", save_run_state(Path(d), obj["fs"], obj["rules"]))
