# Attack labels

`A12_attack_list.csv` – the 11 attacks of SWaT.A12 with their label windows in the time of the recording
(the iTrust information sheet is about 25 minutes earlier than the data; these windows already include the shift).
Columns: `attack_id, name, targets, label_start, label_end, seconds_in_data`.

This file is the single source of the attack times. It is used for the evaluation (`swatad.data.a12_attacks`) and to build the
per-second label file (`python scripts/rebuild_a12_labels.py`). It is deliberately **not** part of the knowledge base: the
attack catalog the explainer reads (`knowledge_base/04_a12_attack_catalog.md`) contains the durations but no clock times, so an
explainer cannot find the right attack by matching the time of an event.
