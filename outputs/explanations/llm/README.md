# Output of the Claude explanation backend (it was run)

`Explainer(backend="claude")` was run on the 10 alarm events of the A12 window-AE + rules detector
(`outputs/anomalies/a12_A11-A10_noAIT__WinAE.json`). Every record has `"backend": "claude"` (model `claude-opus-5-5`,
adaptive thinking, one call per event). The comparison with the template backend is in
[docs/llm_vs_template_report.md](../../../docs/llm_vs_template_report.md).

| File | Run |
|---|---|
| `claude_with_attack_times.json` | first run, the attack catalog still contained the clock times of the attacks |
| `claude_no_attack_times.json` | clock times removed from the catalog (control experiment, report section 7) |
| `claude_no_attack_times_tag_retrieval_calibrated.json` | no clock times, tag-boosted retrieval, corrected tag dictionary, calibrated confidence (`confidence_raw` is the model's own value) |
| `template_for_comparison.json` | template backend, same events, for comparison |

The records contain the explanation only (no ground truth). They can be regenerated with
`python scripts/export_and_explain.py a12_A11-A10_noAIT WinAE` and `ANTHROPIC_API_KEY` set.
