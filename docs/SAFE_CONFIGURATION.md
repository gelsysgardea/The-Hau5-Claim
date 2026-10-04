# Safe configuration after credential removal

This historical bot reads credentials from process environment variables. Its configuration no longer contains account keys or browser cookies.

Required environment variables: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID. Browser-based Binance requests also require the currently valid BINANCE_COOKIE, CSRF_TOKEN, BNC_UUID, DEVICE_INFO, FVIDEO_ID, FVIDEO_TOKEN, X_TRACE_ID and X_UI_REQUEST_TRACE.

Set these only on your own machine. Do not put real values in tracked files, issues or pull requests. The .gitignore rules do not untrack a file that was already committed.

Previously published credentials must be revoked or rotated by their providers. Removing their source literals does not invalidate copies already fetched from repository history. A separate history-cleaning preparation is being retained privately.

This repository is historical; the maintained NEXUS deployment is gelsysgardea/Le-Cryptobot. Do not start multiple claim engines against the same account.
