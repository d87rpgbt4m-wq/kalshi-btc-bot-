# BTC bot recovery patch (paper-only)

A small BTC-only entry-policy overlay based on the production journal audit dated 2026-10-26.

**Not a full source backup and not currently deployed.** GitHub rejected access due to an account suspension, and Render refused environment changes because it could not access the repository. Restore legitimate source access before integrating/redeploying.

The conservative gate requires a fresh signal, confirmed volume, aligned trend and momentum, score >=45 (heuristic, not probability), entry ask <=75¢, spread <=2¢, no chase warning, current trend data, stop-loss and take-profit protection, and paper mode. It is intentionally configurable for controlled tests.

Run tests with:

```bash
python -m unittest discover -s tests -v
```

See `BTC_PERFORMANCE_AUDIT.md` for actual historical performance and holdout caveats, and `INTEGRATION_GUIDE.md` for integration/deployment steps.
