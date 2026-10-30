# Buildmart API

<p>
  <strong>A role-aware marketplace backend for construction materials, buyer-seller messaging, payments, moderation, and community activity.</strong>
</p>

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.15-a30000)
![License](https://img.shields.io/badge/License-AGPL--3.0-blue)
![Database](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)

Buildmart is a Django REST Framework marketplace API designed for Kenyan and regional construction supply businesses. It combines email-first authentication, three user roles, product catalog management, seller verification, boost plans, Flutterwave payment initiation, direct messaging models, product questions and answers, notifications, reporting, disputes, and activity tracking.

This repository contains the backend. It is suitable for API-first clients, mobile applications, dashboards, and integrations.

## Highlights

- Email and JWT authentication with refresh-token rotation
- Google OAuth integration through django-allauth and dj-rest-auth
- User, seller, and administrator role boundaries
- Seller onboarding and verification workflows
- Hierarchical categories and marketplace products
- Product reviews, inventory quantities, boosted listings, and product images
- Automatic image resizing, thumbnails, and upload cleanup using Pillow
- Flutterwave checkout initiation and webhook handling for boosted listings
- Buyer-seller chats, message records, product Q&A, and helpful-answer votes
- User notifications, system notifications, and contact submissions
- User and seller activity feeds
- Reports, flags, disputes, and dispute messages
- Django admin support for operational management
- UUID identifiers for marketplace entities and tokens for API access

## Technology Stack

| Layer | Technology |
|---|---|
| Language | Python 3.8+ |
| Web framework | Django 4.2 |
| API framework | Django REST Framework 3.15 |
| Authentication | Simple JWT, dj-rest-auth, django-allauth |
| Database | SQLite for local development |
| Media processing | Pillow |
| CORS | django-cors-headers |
| Payments | Flutterwave HTTP API |
| Social login | Google OAuth 2.0 |

## Architecture

```text
Clients (Web / Mobile / Admin)
            |
            v
       Django REST API
            |
   +--------+----------------+
   |        |                |
 Accounts  Products        Payments
   |        |                |
   +---- Chats / Reports ----+
   |        |                |
Notifications  Activities   SQLite / Filesystem
```

### Django Applications

| App | Responsibility |
|---|---|
| `accounts` | Email user model, profiles, sellers, verification, registration, login, passwords, and Google OAuth |
| `products` | Categories, listings, inventory, images, reviews, and boost metadata |
| `payments` | Boost plans, listing boosts, Flutterwave payment initiation, and webhook processing |
| `chats` | Buyer-seller chats, messages, product questions, answers, and helpful votes |
| `notifications` | System notifications, per-user read state, and contact messages |
| `activities` | Recent seller/buyer activity and product-view tracking |
| `reports` | Content reports, flags, moderation records, disputes, and dispute messages |

## API Overview

The API uses `/api/<application>/...` prefixes. The development server defaults to `http://127.0.0.1:8000`.

| Area | Base path | Main capabilities |
|---|---|---|
| Accounts | `/api/accounts/` | Registration, login, logout, JWT refresh, email verification, passwords, profiles, sellers |
| Products | `/api/products/` | Categories, products, product images, reviews, and seller catalog operations |
| Payments | `/api/payments/` | Boost plans, boost purchases, payment status, Flutterwave webhook |
| Chats | `/api/chats/` | Chats, messages, questions, answers, and helpful votes |
| Notifications | `/api/notifications/` | Admin/user notifications and contact submissions |
| Activities | `/api/activities/` | Buyer activity and admin activity feeds |
| Reports | `/api/reports/` | Reports, flags, disputes, and dispute messages |
| Admin | `/admin/` | Django administration interface |
| OAuth routes | `/accounts/` | django-allauth provider and account routes |
| Media | `/media/` | Uploaded files served by Django in debug mode |

## Authentication

Buildmart uses JWT authentication:

- Access token lifetime: 60 minutes
- Refresh token lifetime: 7 days
- Refresh-token rotation is enabled
- Refresh tokens are invalidated after rotation
- Tokens use the `Bearer` authorization header

```http
Authorization: Bearer <access-token>
Content-Type: application/json
```

Example login:

```bash
curl -X POST http://127.0.0.1:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"replace-with-a-real-password"}'
```

Example authenticated request:

```bash
curl http://127.0.0.1:8000/api/accounts/profile/ \
  -H "Authorization: Bearer <access-token>"
```

By default, DRF is configured for JWT and session authentication. Open the route modules below to inspect permissions and action-level authorization for each resource:

- `accounts/urls.py`
- `products/urls.py`
- `payments/urls.py`
- `chats/urls.py`
- `notifications/urls.py`
- `activities/urls.py`
- `reports/urls.py`

## Key Domain Models

- `CustomUser`: email-based account identity and `user`, `seller`, or `admin` role
- `Profile`: personal profile for regular users and administrators
- `Seller`: business profile, address, verification status, and subscription state
- `Category`: hierarchical product category
- `Product`: marketplace listing with price, quantity, seller, category, and boost state
- `ProductImage`: optimized listing image, thumbnail, dimensions, and display order
- `ProductReview`: one verified-purchase-aware review per user per product
- `BoostPlan` / `Boost`: promoted-listing packages and payment state
- `Chat` / `Message`: buyer-seller conversations
- `ProductQuestion` / `ProductAnswer`: listing Q&A and seller answers
- `Notification` / `NotificationRead`: notifications and per-user read state
- `RecentActivity`: recent marketplace events
- `Report` / `Flag` / `Dispute`: moderation and resolution records

## Local Development

### Requirements

- Python 3.8 or newer
- `pip` and `venv`
- A Google OAuth client for social-login testing, optional
- A Flutterwave account for payment testing, optional

### Setup

```bash
git clone https://github.com/Kiprotich-Code/buildmart.git
cd buildmart

python -m venv .venv
```

Activate the virtual environment:

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

Install dependencies and initialize the database:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.

### Environment Variables

Copy `.env.example` to `.env`, then replace placeholders before using protected integrations.

```dotenv
# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@buildmart.com

# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your-google-client-secret

# Flutterwave
FLUTTERWAVE_PUBLIC_KEY=your-flutterwave-public-key
FLUTTERWAVE_SECRET_KEY=your-flutterwave-secret-key
```

The settings module also contains local defaults for development. Review and replace secrets and host restrictions before deployment.

> Important: the current settings module is development-oriented. It currently uses a fixed SQLite database and development secret values, permits all CORS origins, enables debug mode, and serves media locally. Configure environment-backed settings and HTTPS before production deployment.

## Common Operations

### Create an administrator

```bash
python manage.py createsuperuser
```

### Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Load sample chat data

```bash
python manage.py create_chat_test_data
```

### Load sample activities

```bash
python manage.py create_sample_activities
```

### Django shell

```bash
python manage.py shell
```

## Testing

Run the complete Django test suite:

```bash
python manage.py test
```

Run a single app:

```bash
python manage.py test accounts
python manage.py test products
python manage.py test payments
python manage.py test reports
python manage.py test notifications
```

Run with fail-fast behavior while developing:

```bash
python manage.py test --failfast
```

The repository includes application-level tests across authentication, payments, reports, notifications, and other marketplace areas. Some standalone test scripts are also present at the project root; prefer the Django test runner for repeatable suite execution.

## Payments and Webhooks

Boost purchases are created through the payments API. The payment flow uses a generated transaction reference and Flutterwave keys loaded from the environment.

After deployment:

1. Configure the Flutterwave keys.
2. Register the public webhook URL with Flutterwave.
3. Verify that the deployed webhook receives HTTPS requests.
4. Record and reconcile the returned transaction reference before activating boosts.
5. Use provider signature verification or server-side transaction verification as part of hardening.

The webhook route is:

```text
/api/payments/webhook/flutterwave/
```

## Product Images

Product image handling is implemented in the `products` app:

- Up to 5 MB upload size is configured
- Supported types include JPEG, PNG, and WebP
- Main images are resized and optimized
- Thumbnails are generated through Pillow
- Dimensions and file size are stored on `ProductImage`
- Image files are removed when image records are deleted
- Images and thumbnails are served from `MEDIA_ROOT` during development

For production, configure persistent object storage or a shared media volume; a local filesystem is not appropriate for stateless application instances.

## Real-Time Routing

The chats app defines WebSocket consumers and URL patterns for chat, dispute, and user events. Before enabling them in production, wire Django Channels into `ASGI_APPLICATION`, add `channels` and a channel-layer backend such as Redis, register the routing layer, configure authentication, and run a documented ASGI server.

## Project Structure

```text
buildmart/
├── accounts/       Authentication, users, profiles, sellers
├── activities/     Recent activity and view tracking
├── chats/          Chat, messages, product Q&A
├── notifications/  Notifications and contact submissions
├── payments/       Boost plans and Flutterwave payments
├── products/       Catalog, listings, images, reviews
├── reports/        Reports, flags, disputes
├── buildmart/      Project settings, root routes, WSGI/ASGI
├── media/          Local uploaded media
├── manage.py       Django management entry point
├── requirements.txt Python dependencies
└── .env.example    Example environment variables
```

## Production Checklist

Before exposing this API publicly:

- [ ] Replace the Django secret key and load it from environment variables
- [ ] Set `DEBUG=False`
- [ ] Restrict `ALLOWED_HOSTS`
- [ ] Replace permissive CORS settings with explicit origins
- [ ] Configure `DATABASE_URL` or the intended production database and migrations
- [ ] Configure HTTPS, secure cookies, HSTS, and proxy headers
- [ ] Use persistent media storage and a CDN or signed storage URLs when appropriate
- [ ] Configure SMTP credentials from secrets management
- [ ] Set a strict payment webhook verification strategy
- [ ] Add request throttling and centralized logging
- [ ] Configure backups, monitoring, health checks, and error reporting
- [ ] Review permissions, object-level authorization, and admin access
- [ ] Run migrations and tests in CI before deployment

## API Documentation

There is no OpenAPI/Swagger dependency or generated schema currently declared in `requirements.txt`. For publication-ready documentation, add `drf-spectacular`, generate an OpenAPI schema, and serve versioned interactive documentation.

The URL module is the source of truth for current routes. For payment integration details, see `payments/API_TESTING_GUIDE.md` only if present in the deployed branch; general API behavior should be documented from the route and serializer implementations.

## Security

- Do not commit `.env`, database files, private keys, payment secrets, or generated media
- Do not expose the Django admin without network, authentication, and operational controls
- Use strong passwords and rotate OAuth/payment credentials regularly
- Validate provider callbacks against verified transaction/server-side data
- Review role checks and object-level permissions when adding endpoints
- Report suspected vulnerabilities privately to the repository maintainer

## Contributing

Contributions should preserve the existing Django app boundaries and API conventions.

1. Create a focused branch from `main`.
2. Add or update migrations for model changes.
3. Add tests covering authorization, validation, and regressions.
4. Run the smallest relevant Django test module first.
5. Run the full suite before opening a pull request.
6. Keep secrets, generated databases, media, and test fixtures out of commits.

```bash
git checkout -b feature/short-description
python manage.py test
git add .
git commit -m "feat: add short description"
git push origin feature/short-description
```

## License

Buildmart is licensed under the **GNU Affero General Public License v3.0**. See [LICENSE](./LICENSE) for the complete terms.

Copyright (C) 2026 Kiprotich-Code and contributors.
