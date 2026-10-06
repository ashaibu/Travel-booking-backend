# ASAA Travel — Python Edition

A straight port of the Go/Gin version to Python/Flask — same routes, same
in-memory data, same behavior. If you know the Go version, nothing here
will surprise you; `main.py` is the `main.go` of this project.

| Go concept | Python equivalent |
|---|---|
| Gin router + handler funcs | Flask `@app.get`/`@app.post` decorators |
| `html/template` | Jinja2 (`templates/`, same files, `{{.Field}}` → `{{ field }}`) |
| `sync.Mutex` | `threading.Lock` |
| `map[string]User` | `dict` |
| `[]TicketApplication` | `list[dict]` |
| `go run .` | `python main.py` |

## Running it locally

```bash
pip install -r requirements.txt --break-system-packages   # or use a venv
python main.py
```

Visit `http://localhost:8080`.

- Customer demo login: `traveler@example.com` / `user123`
- Admin login (same form): `admin` / `adminpassword123`

## Features (same as the Go version)

- **One login form for everyone.** `/login` posts to `/api/auth/login`,
  which checks admin credentials first, then falls back to customer
  accounts, and tells the frontend which role matched. No separate
  Admin Portal link anywhere in the nav.
- **Admin can create AND edit price tags.** The pricing table on
  `/admin` has an Edit button per row; submitting the form again for
  the same destination+mode overwrites the price (upsert by key).
- **NGN checkout.** Flutterwave checkout runs in Naira with
  `card, banktransfer, ussd, account` as payment options (the right
  set for Nigeria).
- **"My Tickets" page.** Logged-in customers see their own application
  history at `/my-tickets`, filtered server-side by their email.
- **Secrets via environment variables**, with local-dev fallbacks so
  running it untouched still works. Same variable names as the Go
  version — see the table below.

## Environment variables (for deployment, e.g. Render)

| Key | Purpose |
|---|---|
| `ADMIN_USERNAME` | Admin login identifier |
| `ADMIN_PASSWORD` | Admin login password |
| `SMTP_EMAIL` | "From" address for ticket emails |
| `SMTP_APP_PASSWORD` | App password for that mailbox |
| `SMTP_HOST` | SMTP server (default `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default `587`) |
| `FLUTTERWAVE_PUBLIC_KEY` | Your Flutterwave **publishable** key |

`PORT` is injected automatically by most hosts (including Render) —
the app reads it, you don't need to set it yourself.

## Deploying on Render

Same idea as the Go version, different start command:

- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python main.py`

Everything else — the Environment Variables tab, the deploy flow — works
exactly the way it did for the Go service.

## Known gaps (carried over from the Go version, not fixed here)

- "Sessions" are just a flag in `localStorage` — no real server-side
  session/token. Not production-grade auth.
- All data (users, applications, pricing) is in-memory and resets on
  restart — no database.
- Passwords are stored in plaintext in memory.
