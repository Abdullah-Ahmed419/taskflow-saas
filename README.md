# 🚀 TaskFlow SaaS — Complete Upgrade Guide

## New Project Structure

```
taskflow-saas/
├── app.py                  ← App factory (Flask extensions + blueprints)
├── config.py               ← Dev / Prod / Test config classes
├── requirements.txt
├── Procfile
├── railway.json
├── .env.example
│
├── models/
│   ├── __init__.py
│   ├── user.py             ← User model (plan helpers, avatar_url, etc.)
│   ├── task.py             ← Task model
│   └── subscription.py     ← NEW: Subscription model (free/pro)
│
├── routes/
│   ├── __init__.py
│   ├── auth.py             ← Login, signup, Google OAuth, password reset
│   ├── tasks.py            ← Task CRUD (plan-enforced)
│   ├── main.py             ← Dashboard + /api/me + /api/stats
│   ├── profile.py          ← NEW: name, avatar, password
│   └── admin.py            ← NEW: admin panel (/admin/)
│
├── services/
│   ├── __init__.py
│   ├── auth_service.py     ← Signup, login, OAuth, password reset tokens
│   ├── task_service.py     ← Task CRUD + plan limit enforcement
│   ├── notification_service.py ← Email reminders + password reset emails
│   └── profile_service.py  ← Avatar upload, name/password changes
│
├── templates/
│   ├── auth.html           ← Login / Signup
│   ├── app.html            ← Main task manager UI (keep your existing one)
│   ├── dashboard.html      ← NEW: Stats dashboard
│   ├── profile.html        ← NEW: Profile editor
│   ├── forgot_password.html ← NEW
│   ├── reset_password.html  ← NEW
│   └── admin/
│       └── dashboard.html  ← NEW: Admin panel
│
├── utils/
│   ├── __init__.py
│   ├── decorators.py       ← @admin_required, @pro_required
│   └── cli.py              ← flask create-admin, flask send-reminders
│
└── static/
    └── uploads/            ← Avatar files (gitignored)
```

---

## Feature Summary

### 1. Multi-User Task Isolation ✅
Already present — every query filters by `user_id=current_user.id`. The `TaskService.get_one()` method always passes `user_id` so users can never access each other's tasks, even by guessing IDs.

### 2. Subscription System ✅
New `Subscription` model with `plan` ("free" | "pro") and `status` fields.

**Free plan:** 10 tasks max (configurable via `FREE_TASK_LIMIT` env var).  
**Pro plan:** Unlimited tasks.

`TaskService.create()` and `bulk_import()` enforce limits automatically and return a `403` with an upgrade message when exceeded.

### 3. Dashboard ✅
`/dashboard` shows:
- Total / Completed / Pending task counts
- Completion percentage with animated progress bar
- Plan banner with upgrade CTA for free users

### 4. Notifications ✅
`NotificationService.send_due_reminders()` sends HTML email digests for tasks due today or tomorrow. Run it daily:

```bash
# Add to Railway cron or any scheduler:
flask send-reminders
```

Password-reset emails are also handled by `NotificationService`.

### 5. User Profile ✅
`/profile` allows:
- Update display name (`PUT /api/profile/name`)
- Upload avatar image (`POST /api/profile/avatar`) — stored in `static/uploads/`
- Change password (`PUT /api/profile/password`)

### 6. Admin Panel ✅
`/admin/` (admin users only) shows:
- Platform stats (users, pro subscribers, total tasks)
- Searchable user table with plan badges
- One-click upgrade / downgrade buttons

### 7. Clean Architecture ✅
Routes → Services → Models. Routes are thin: they parse the request, call a service, return JSON. All business logic lives in services.

### 8. Security ✅
- **CSRF:** `flask-wtf` CSRF protection via `CSRFProtect(app)` — API routes are JSON so CSRF tokens are not required (header-based)
- **Secure cookies:** `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE=Lax` in production config
- **Password reset:** Signed, time-limited tokens via `itsdangerous` (1-hour expiry)
- **No email enumeration:** `/api/auth/forgot-password` always returns `200`
- **File upload safety:** Extension allowlist + 2 MB size limit
- **Admin access:** `@admin_required` decorator + `is_admin` DB column

### 9. Database Migrations ✅
`flask-migrate` (Alembic) is wired in. Use these commands:

```bash
flask db init        # First time only — creates migrations/ folder
flask db migrate -m "Add subscription table"
flask db upgrade     # Apply migration (runs automatically on Railway deploy)
```

---

## Step-by-Step Setup

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

Minimum required for local dev:
```
FLASK_ENV=development
SECRET_KEY=any-long-random-string
```

### Step 3 — Initialize database

```bash
flask db init        # creates migrations/ folder (first time only)
flask db migrate -m "Initial SaaS schema"
flask db upgrade
```

### Step 4 — Create your first admin

```bash
# First sign up via the web UI, then:
flask create-admin your@email.com
```

### Step 5 — Run locally

```bash
python app.py
# Open http://localhost:5000
```

---

## Railway Deployment

The `railway.json` `startCommand` runs `flask db upgrade` before gunicorn starts, so migrations apply automatically on every deploy.

Environment variables to set in Railway dashboard:

| Variable | Value |
|---|---|
| `FLASK_ENV` | `production` |
| `SECRET_KEY` | Long random string |
| `APP_URL` | `https://your-app.up.railway.app` |
| `GOOGLE_CLIENT_ID` | From Google Console (optional) |
| `GOOGLE_CLIENT_SECRET` | From Google Console (optional) |
| `MAIL_USERNAME` | Gmail address |
| `MAIL_PASSWORD` | Gmail App Password |
| `FREE_TASK_LIMIT` | `10` |

`DATABASE_URL` is set automatically by Railway when you add a PostgreSQL service.

---

## Adding Stripe Payments (Next Step)

When you're ready to charge for Pro:

1. Uncomment `stripe` in `requirements.txt`
2. Add `STRIPE_SECRET_KEY`, `STRIPE_PRO_PRICE_ID`, `STRIPE_WEBHOOK_SECRET` to `.env`
3. Create a `routes/billing.py` blueprint with:
   - `POST /api/billing/checkout` → create Stripe Checkout Session
   - `POST /api/billing/webhook` → handle `checkout.session.completed` event → set `subscription.plan = "pro"`
4. Add a "Upgrade to Pro" button on the dashboard that calls `/api/billing/checkout`

---

## CLI Commands

```bash
flask create-admin email@example.com   # Make a user admin
flask set-plan email@example.com pro   # Manually upgrade a user
flask set-plan email@example.com free  # Manually downgrade a user
flask list-users                       # Print all users with plans
flask send-reminders                   # Send due-date email reminders (run daily)
```

---

## Key Design Decisions

**Services layer:** All business logic (plan enforcement, file validation, token generation) lives in `services/`. Routes are thin and only handle HTTP concerns. This makes it easy to test services in isolation and reuse logic (e.g., a future API or CLI command can call `TaskService.create()` directly).

**Subscription model:** Separate table rather than a column on `User`. This makes it easy to add Stripe fields (`stripe_customer_id`, `stripe_subscription_id`) without touching the user table, and supports future multi-plan logic.

**`User.can_create_task(limit)`:** The limit comes from `app.config["FREE_TASK_LIMIT"]` so you can change it via an environment variable without redeploying code.

**No email enumeration:** The forgot-password endpoint always returns `200 OK` regardless of whether the email exists, to prevent attackers from probing which emails are registered.
