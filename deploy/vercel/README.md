# ANVAYA Vercel entry point

This Vercel project serves a small entry page that immediately opens the working
ANVAYA service on Render. The Python application, sessions and synthetic SQLite
demonstration data run in one process on Render; Vercel supplies a short public
entry URL without duplicating the stateful backend.
