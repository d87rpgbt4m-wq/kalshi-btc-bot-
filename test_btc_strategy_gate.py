import unittest
from dataclasses import replace

from btc_strategy_gate import BTCEntryContext, BTCEntryPolicy, evaluate_btc_entry


class BTCStrategyGateTests(unittest.TestCase):
    def setUp(self):
        self.good = BTCEntryContext(
            direction="UP",
            signal_age_seconds=20,
            internal_score=55,
            entry_ask_cents=68,
            spread_cents=1,
            trend_bias="UP",
            trend_alignment="aligned",
            momentum_alignment="aligned",
            trend_snapshot_age_seconds=5,
            volume_confirmation=True,
            chase_warning=False,
            stop_loss_enabled=True,
            take_profit_enabled=True,
            live_trading_enabled=False,
            seconds_remaining=600,
        )

    def test_clean_paper_candidate_passes(self):
        result = evaluate_btc_entry(self.good)
        self.assertTrue(result.allowed, result.reason_text)
        self.assertTrue(result.paper_only)
        self.assertFalse(result.is_probability_estimate)
        self.assertEqual(result.policy_version, "btc_hybrid_quality_gate_v1")

    def test_low_internal_score_is_not_treated_as_a_probability(self):
        result = evaluate_btc_entry(replace(self.good, internal_score=27))
        self.assertFalse(result.allowed)
        self.assertTrue(any("not a probability" in reason for reason in result.reasons))

    def test_entry_price_above_75_cents_is_rejected(self):
        result = evaluate_btc_entry(replace(self.good, entry_ask_cents=76))
        self.assertFalse(result.allowed)
        self.assertTrue(any("ceiling" in reason for reason in result.reasons))

    def test_unknown_or_missing_volume_confirmation_fails_closed(self):
        for value in (None, False):
            with self.subTest(value=value):
                result = evaluate_btc_entry(replace(self.good, volume_confirmation=value))
                self.assertFalse(result.allowed)
                self.assertTrue(any("volume confirmation" in reason for reason in result.reasons))

    def test_non_aligned_trend_or_momentum_is_rejected(self):
        self.assertFalse(evaluate_btc_entry(replace(self.good, trend_alignment="opposed")).allowed)
        self.assertFalse(evaluate_btc_entry(replace(self.good, momentum_alignment="mixed")).allowed)

    def test_signal_and_feature_snapshot_must_be_fresh(self):
        self.assertFalse(evaluate_btc_entry(replace(self.good, signal_age_seconds=91)).allowed)
        self.assertFalse(evaluate_btc_entry(replace(self.good, trend_snapshot_age_seconds=46)).allowed)

    def test_missing_stop_loss_or_take_profit_blocks_main_cohort(self):
        self.assertFalse(evaluate_btc_entry(replace(self.good, stop_loss_enabled=False)).allowed)
        self.assertFalse(evaluate_btc_entry(replace(self.good, take_profit_enabled=False)).allowed)

    def test_wide_spread_or_active_chase_warning_is_rejected(self):
        self.assertFalse(evaluate_btc_entry(replace(self.good, spread_cents=3)).allowed)
        self.assertFalse(evaluate_btc_entry(replace(self.good, chase_warning=True)).allowed)
        self.assertFalse(evaluate_btc_entry(replace(self.good, chase_warning=None)).allowed)

    def test_opposing_direction_and_unavailable_direction_are_rejected(self):
        self.assertFalse(evaluate_btc_entry(replace(self.good, trend_bias="DOWN")).allowed)
        self.assertFalse(evaluate_btc_entry(replace(self.good, direction="UNKNOWN")).allowed)

    def test_late_entries_are_rejected(self):
        self.assertFalse(evaluate_btc_entry(replace(self.good, seconds_remaining=60)).allowed)

    def test_live_mode_is_always_rejected_by_this_paper_gate(self):
        result = evaluate_btc_entry(replace(self.good, live_trading_enabled=True))
        self.assertFalse(result.allowed)
        self.assertTrue(result.paper_only)

    def test_nonfinite_values_fail_closed(self):
        result = evaluate_btc_entry(replace(self.good, entry_ask_cents=float("nan")))
        self.assertFalse(result.allowed)
        self.assertTrue(any("invalid" in reason for reason in result.reasons))

    def test_policy_can_be_tightened_without_source_changes(self):
        policy = BTCEntryPolicy(min_internal_score=60, max_entry_cents=70)
        result = evaluate_btc_entry(replace(self.good, entry_ask_cents=72), policy)
        self.assertFalse(result.allowed)
        self.assertTrue(any("below 60" in reason for reason in result.reasons))
        self.assertTrue(any("70.00c ceiling" in reason for reason in result.reasons))


if __name__ == "__main__":
    unittest.main()
