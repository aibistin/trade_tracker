---
name: deploy-production
description: Deploy or manage this project's production systemd services (trade_tracker backend, trade_tracker_front frontend) — restarting after a code change, checking status, or tailing logs. Use when the user asks to deploy, restart production, check service status, or view production logs for the Trading app.
---

Service files live in `util/`. After editing, copy to `/etc/systemd/system/` and reload:
```bash
sudo cp util/trade_tracker.service /etc/systemd/system/
sudo cp util/trade_tracker_front.service /etc/systemd/system/
sudo systemctl daemon-reload

sudo systemctl start trade_tracker        # Flask/gunicorn backend on port 3000
sudo systemctl start trade_tracker_front  # Vite preview frontend on port 4173
sudo systemctl status trade_tracker
sudo systemctl status trade_tracker_front
journalctl -u trade_tracker -f            # Real-time backend logs
journalctl -u trade_tracker_front -f      # Real-time frontend logs
```
- **`util/trade_tracker.service`** — runs `gunicorn --bind 127.0.0.1:3000` with `FLASK_ENV=production`
- **`util/trade_tracker_front.service`** — runs `pnpm run preview` (Vite preview, `strictPort: true` on 4173)
- Production frontend is built with `pnpm build` (from `frontend/`), which picks up `frontend/.env.production` setting `VITE_API_BASE_URL=http://localhost:3000/api`
- Dev frontend (`pnpm dev`) uses the default `src/config.js` URL (`http://localhost:5000/api`)
