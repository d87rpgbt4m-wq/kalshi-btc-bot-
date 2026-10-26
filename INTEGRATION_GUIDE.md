# Integrating the BTC quality gate

This folder is a **BTC-only patch overlay**, not a complete replacement for the original repository. The original repo source could not be retrieved through GitHub while its owner account was suspended, so do not overwrite the main app with these files alone.

## What to add

- `btc_strategy_gate.py` — pure, fail-closed paper-entry policy.
- `tests/test_btc_strategy_gate.py` — deterministic unit tests.
- `BTC_PERFORMANCE_AUDIT.md` — audited current database results and the reason not to promote the candidate.

## Where to call the gate

In the existing worker's hybrid alert path, call `evaluate_btc_entry(...)` **after** fetching a fresh valid market quote and constructing the trend/volume/momentum snapshot, but **before** creating/inserting a paper position. Construct `BTCEntryContext` from the actual values used by the current decision. Do not substitute missing fields with fabricated defaults. Map `volume_confirmation` to `True` only when the measured condition is explicitly confirmed; use `None` for unknown.

Example integration (adapt field names to the real worker code):

```python
from btc_strategy_gate import BTCEntryContext, evaluate_btc_entry

entry_gate = evaluate_btc_entry(BTCEntryContext(
    direction=signal.direction,
    signal_age_seconds=signal.age_seconds,
    internal_score=decision.internal_score,
    entry_ask_cents=quote.ask_cents,
    spread_cents=quote.spread_cents,
    trend_bias=features.trend_bias,
    trend_alignment=features.trend_alignment,
    momentum_alignment=features.momentum_alignment,
    trend_snapshot_age_seconds=features.snapshot_age_seconds,
    volume_confirmation=features.volume_confirmation,  # True/False/None
    chase_warning=features.chase_warning,               # True/False/None
    stop_loss_enabled=paper_config.stop_loss_enabled,
    take_profit_enabled=paper_config.take_profit_enabled,
    live_trading_enabled=False,
    seconds_remaining=market.seconds_remaining,
))

if not entry_gate.allowed:
    # Persist the exact reasons to the normal signal/decision audit and DO NOT open.
    audit_signal_decision("vetoed", entry_gate.as_dict())
    return {"action": "vetoed", "reason": entry_gate.reason_text}

# Continue through all the existing independent exposure, quote, fee, and paper-only checks.
```

**Important:** this block is an integration example; the original source-level insertion could not be made or deployed from this session. Use the actual project dataclasses/fields and keep all independent risk checks. Never treat `internal_score` as a win probability.

## Suggested runtime settings for the main paper cohort

Use the Render dashboard after source/repository access is restored:

```env
PAPER_STOP_LOSS_ENABLED=true
PAPER_TREND_STOP_LOSS_ENABLED=true
PAPER_TREND_STOP_SHADOW_MODE=false
PAPER_TAKE_PROFIT_ENABLED=true
REAL_ORDER_ADAPTER_INSTALLED=false
LIVE_APPROVAL_RECORDED=false
```

The existing no-stop-loss test was negative in the live paper journal, so don't use that configuration for the main paper cohort. If you still need to test the hypothesis, record a separate hold-to-settlement shadow result for the *same entries*, without changing the main cohort's risk handling. Verify the worker startup/config log before trusting any new trades.

## Test

From this folder:

```bash
python -m unittest discover -s tests -v
```

Passing these unit tests does not prove the trading rule is profitable. Compare it prospectively with the incumbent over the same eligible signals and promote only after sufficient settled out-of-sample evidence.
