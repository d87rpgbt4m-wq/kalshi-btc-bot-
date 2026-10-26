# BTC bot performance audit — 26 October 2026

## Production data checked

The currently available Render database shows 112 settled trades tagged `entry_signal_source='hybrid'`:

- 65 positive trades, 46 negative trades, and one flat trade.
- Net P&L: **−476.8¢** (−$4.768), average **−4.26¢ per trade**.
- Average positive trade: **+17.15¢**.
- Average negative trade: **−34.60¢**.
- Win percentage is approximately 58%, but average losses are about twice the average win. Win rate by itself is an inadequate objective.

The newest five trades (IDs 161–165) netted **−202¢**, with two positive and three negative outcomes. Trades 151–165, the no-stop-loss experiment cohort, netted **−177¢** across 15 settled trades. All 15 had a null `stop_loss_cents` field. The worker log for trade 165 explicitly reported `trend_stop_enabled=False`; trade 165 entered at 60¢ with internal score 27 and lost 62¢ at settlement.

The decision audit records entries where the external TradingView/GainzAlgo direction passed because the internal engine did not detect a configured *major contradiction*. The audit message explicitly says that an ordinary low score is not itself a veto in hybrid mode. That behavior is too permissive when the internal score is a heuristic, not a calibrated win probability.

## Candidate filter evaluation (retrospective only)

A proposed strict entry filter requiring (a) internal score >= 45, (b) entry ask <= 75¢, (c) confirmed volume, (d) aligned trend, (e) aligned momentum, and (f) no chase warning would have selected 16 of the 112 historical hybrid trades: 11 winners and five losses, net **+27.2¢** in that total selected sample.

The chronology split warns against promoting it:

| Period by trade ID | Filtered trades | Win/loss | Net P&L |
|---|---:|---:|---:|
| Older, IDs <=110 | 5 | 2 / 3 | −42.8¢ |
| Middle, IDs 111–140 | 8 | 7 / 1 | +86.0¢ |
| Recent, IDs 141–165 | 3 | 2 / 1 | −16.0¢ |

This sample is very small and the recent holdout is negative, so **the filter is a candidate for a prospective paper-only test, not a proven strategy and not eligible for promotion**. The tests here prove only the entry gate's deterministic behavior, not trading profitability.

## Recommended recovery order

1. Restore stop-loss protection for the main paper cohort; keep take-profit enabled. Keep any no-stop-loss experiment segregated and clearly tagged as a shadow cohort rather than mixing it with the primary results.
2. Add a deterministic pre-entry gate; do not let an external UP/DOWN alert alone bypass weak/unknown volume or weak internal evidence.
3. Save decision reasons for every allowed/rejected signal, and evaluate candidates on identical prospective signals.
4. Require at least 100 prospective settled trades per candidate, realistic fees/spread, positive net P&L, and an out-of-sample confidence-bound check before promotion. A smaller sample can detect obvious bugs, not establish robustness.
5. Keep live order submission disabled.

## Operational limitation

The GitHub connector returned HTTP 403 stating that the repository owner's account is suspended. Render rejected an attempt to update the worker's environment variables with: `Access to the Git repository was denied. Please try disconnecting and reconnecting your GitHub account.` Therefore the configuration change to restore stop loss was **not applied**, and this patch is not deployed. Restore legitimate repository access or connect Render to an accessible, authorized repository before claiming a source-level hotfix is live.
