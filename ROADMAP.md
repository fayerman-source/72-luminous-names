# Roadmap

## Near Term

- Replace generated test-tone MP3 files with reviewed meditation recordings.
- Add persistent users and sessions backed by a database.
- Integrate real checkout and subscription status before reintroducing paid access language.
- Add content review for Hebrew text, transliterations, meanings, and themes.
- Expand automated tests around auth, payments, and deployment behavior.

## Product Improvements

- Add session progress tracking.
- Add search and filters for names, themes, and meanings.
- Improve mobile player controls and accessibility.
- Add admin tooling for managing names and audio assets.

## Production Readiness

- Require `SECRET_KEY` only if cookie-backed features (accounts, saved names) are ever added — never a hardcoded default.
- Enable Vercel Web Analytics so traffic can actually be measured.
- Replace in-memory demo state with durable storage, if accounts return.
- Add structured logging and error monitoring.
- Document asset licensing and contributor permissions for recordings.
