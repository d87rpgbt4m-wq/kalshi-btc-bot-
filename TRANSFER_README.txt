KALSHI BTC BOT — TRANSFER BUNDLE
================================

WHAT IS IN THIS ZIP
-------------------
• The full 121-file BTC bot source snapshot saved on 2026-10-24, at the repository root.
• A separate RECOVERY_PATCH_2026-10-26 folder containing the small BTC strategy-gate patch saved on 2026-10-26.
• The recovery patch is kept separate and is NOT automatically wired into the baseline app.

IMPORTANT SOURCE-VERSION LIMITATION
----------------------------------
This is NOT a byte-for-byte export of the latest GitHub main branch. During the export attempt on 2026-10-26, GitHub's API returned HTTP 403 with the message "Sorry. Your account was suspended" and the main-branch archive URL returned Not Found. Therefore the latest post-2026-10-24 commits could not be fetched to construct a faithful current-source export.

Use this bundle as a restorable full source snapshot, not as proof that it contains every change deployed on 2026-10-26. The RECOVERY_PATCH_2026-10-26 folder contains a small independent patch and integration guide; review it before copying files into the app root.

REBUILDING THE NEW REPOSITORY
-----------------------------
1. Download and extract this ZIP locally.
2. Create the new empty GitHub repository.
3. Upload the CONTENTS of the extracted folder to the repository root (not the ZIP itself).
4. Keep .github/workflows/ and all source/test files and folders.
5. Do not upload personal/vendor keys or secret files. This bundle intentionally does not include the separate generated app-secrets file or live environment values.
6. Review RECOVERY_PATCH_2026-10-26/INTEGRATION_GUIDE.md before merging that patch into production code.
7. Keep LIVE_TRADING_ENABLED=false and TRADING_MODE=paper while restoring and validating.

BASE SNAPSHOT FILE COUNT
------------------------
The baseline archive contained 121 entries before the recovery patch and transfer notes were added.
