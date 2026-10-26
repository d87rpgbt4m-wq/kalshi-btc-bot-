"""Conservative BTC paper-entry gate for the Kalshi 15-minute hybrid strategy.

This is a deterministic, paper-only quality/risk gate. It does not predict price,
turn an internal score into a probability, submit orders, or guarantee profitability.
Integrate it after a fresh market quote and feature snapshot are available, but before
creating a paper position.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any

POLICY_VERSION = "btc_hybrid_quality_gate_v1"


@dataclass(frozen=True)
class BTCEntryContext:
    direction: str
    signal_age_seconds: float
    internal_score: float
    entry_ask_cents: float
    spread_cents: float
    trend_bias: str
    trend_alignment: str
    momentum_alignment: str
    trend_snapshot_age_seconds: float
    volume_confirmation: bool | None
    chase_warning: bool | None
    stop_loss_enabled: bool
    take_profit_enabled: bool
    live_trading_enabled: bool = False
    seconds_remaining: float | None = None


@dataclass(frozen=True)
class BTCEntryDecision:
    allowed: bool
    policy_version: str
    reasons: tuple[str, ...]
    is_probability_estimate: bool = False
    paper_only: bool = True

    @property
    def reason_text(self) -> str:
        return "; ".join(self.reasons) if self.reasons else "BTC paper-entry quality gate passed."

    def as_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "policy_version": self.policy_version,
            "reasons": list(self.reasons),
            "reason": self.reason_text,
            "is_probability_estimate": self.is_probability_estimate,
            "paper_only": self.paper_only,
        }


@dataclass(frozen=True)
class BTCEntryPolicy:
    """Conservative candidate filter; values are configurable for controlled paper tests."""

    min_internal_score: float = 45.0
    max_entry_cents: float = 75.0
    max_spread_cents: float = 2.0
    max_signal_age_seconds: float = 90.0
    max_trend_snapshot_age_seconds: float = 45.0
    min_seconds_remaining: float = 120.0
    require_volume_confirmation: bool = True
    require_trend_alignment: bool = True
    require_momentum_alignment: bool = True
    require_stop_loss: bool = True
    require_take_profit: bool = True
    paper_only: bool = True


def _valid_number(value: Any) -> bool:
    try:
        return isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def evaluate_btc_entry(
    context: BTCEntryContext,
    policy: BTCEntryPolicy | None = None,
) -> BTCEntryDecision:
    """Return a fail-closed allow/deny decision with explicit audit reasons.

    This gate intentionally rejects unknown required features. Do not replace missing
    feature values with defaults that silently pass an entry.
    """
    policy = policy or BTCEntryPolicy()
    reasons: list[str] = []

    if context.live_trading_enabled or not policy.paper_only:
        reasons.append("live trading is outside this paper-only gate")

    direction = _norm(context.direction).upper()
    if direction not in {"UP", "DOWN"}:
        reasons.append("signal direction must be UP or DOWN")

    numeric_fields = {
        "signal age": context.signal_age_seconds,
        "internal score": context.internal_score,
        "entry ask": context.entry_ask_cents,
        "spread": context.spread_cents,
        "trend snapshot age": context.trend_snapshot_age_seconds,
    }
    for label, value in numeric_fields.items():
        if not _valid_number(value):
            reasons.append(f"{label} is missing or invalid")

    # Only run comparisons for finite numeric fields.
    if _valid_number(context.signal_age_seconds):
        age = float(context.signal_age_seconds)
        if age < 0 or age > policy.max_signal_age_seconds:
            reasons.append(
                f"signal is too old ({age:.1f}s; maximum {policy.max_signal_age_seconds:.1f}s)"
            )
    if _valid_number(context.internal_score):
        score = float(context.internal_score)
        if score < policy.min_internal_score:
            reasons.append(
                f"internal quality score below {policy.min_internal_score:.0f} (got {score:.1f}); score is not a probability"
            )
        if score > 100 or score < 0:
            reasons.append("internal quality score must be between 0 and 100")
    if _valid_number(context.entry_ask_cents):
        price = float(context.entry_ask_cents)
        if not 0 < price <= policy.max_entry_cents:
            reasons.append(
                f"entry ask {price:.2f}c exceeds conservative {policy.max_entry_cents:.2f}c ceiling or is invalid"
            )
    if _valid_number(context.spread_cents):
        spread = float(context.spread_cents)
        if spread < 0 or spread > policy.max_spread_cents:
            reasons.append(f"spread {spread:.2f}c exceeds {policy.max_spread_cents:.2f}c limit")
    if _valid_number(context.trend_snapshot_age_seconds):
        age = float(context.trend_snapshot_age_seconds)
        if age < 0 or age > policy.max_trend_snapshot_age_seconds:
            reasons.append(
                f"trend snapshot is stale ({age:.1f}s; maximum {policy.max_trend_snapshot_age_seconds:.1f}s)"
            )

    if context.seconds_remaining is not None:
        if not _valid_number(context.seconds_remaining):
            reasons.append("market time remaining is missing or invalid")
        else:
            remaining = float(context.seconds_remaining)
            if remaining < policy.min_seconds_remaining:
                reasons.append(
                    f"too little time remains ({remaining:.1f}s; minimum {policy.min_seconds_remaining:.1f}s)"
                )

    trend_bias = _norm(context.trend_bias).upper()
    if direction in {"UP", "DOWN"} and trend_bias != direction:
        reasons.append(f"trend bias does not agree with external direction ({trend_bias or 'unknown'})")
    if policy.require_trend_alignment and _norm(context.trend_alignment) != "aligned":
        reasons.append("timeframe trend alignment is not confirmed")
    if policy.require_momentum_alignment and _norm(context.momentum_alignment) != "aligned":
        reasons.append("momentum alignment is not confirmed")
    if policy.require_volume_confirmation and context.volume_confirmation is not True:
        reasons.append("volume confirmation is missing or false")
    if context.chase_warning is None:
        reasons.append("chase-warning status is unknown")
    elif context.chase_warning:
        reasons.append("chase warning is active")
    if policy.require_stop_loss and not context.stop_loss_enabled:
        reasons.append("stop-loss protection is disabled; refusing new main-cohort entries")
    if policy.require_take_profit and not context.take_profit_enabled:
        reasons.append("take-profit protection is disabled")

    return BTCEntryDecision(
        allowed=not reasons,
        policy_version=POLICY_VERSION,
        reasons=tuple(reasons),
        is_probability_estimate=False,
        paper_only=True,
    )
