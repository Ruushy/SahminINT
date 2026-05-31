# SahminINT

**Passive Reconnaissance & OSINT Web Application**

SahminINT is a locally-hosted, passive reconnaissance platform designed for bug bounty hunters, penetration testers, OSINT researchers, and security professionals. It aggregates publicly available intelligence on domain targets through non-invasive methods — no active scanning, no brute force, and no exploitation.

---

## Overview

SahminINT operates on a **passive intelligence gathering** methodology. Unlike active scanners that send probes directly to a target (which can alert intrusion detection systems or violate scope agreements), SahminINT collects data exclusively from public sources, certificate transparency logs, DNS infrastructure, and search engine indices.

The platform is structured around **recon modules**, each responsible for querying a specific class of public data source. Results are stored locally in a relational database, correlating intelligence to managed target entities.

---

## Modules & Methodology

### Target Management
All reconnaissance is scoped within user-defined **targets** (domains). Targets support tagging, favoriting, and per-target notes for workflow organization and contextual documentation.

### Subdomain Enumeration
Aggregates subdomains entirely from public passive sources with no direct queries to the target:

| Source | Type | Method |
|--------|------|--------|
| [crt.sh](https://crt.sh) | Certificate Transparency Log | Fetches JSON certificate issuances matching `%.domain` |
| [AlienVault OTX](https://otx.alienvault.com) | Threat Intelligence | Queries passive DNS indicators via Open Threat Exchange API |
| [HackerTarget](https://hackertarget.com) | DNS Recon API | Retrieves hostname/IP pairs from reverse DNS |
| [RapidDNS](https://rapiddns.io) | DNS Aggregator | Scrapes subdomain listings from search results |
| [BufferOver](https://dns.bufferover.run) | DNS Reverse Lookup | Queries forward-confirmed and reverse DNS records |
| [Wayback CDX](https://web.archive.org) | Web Archives | Extracts hostnames from archived URLs via the CDX search API |
| [CertSpotter](https://sslmate.com/certspotter) | Certificate Monitoring | Retrieves DNS names from issued SSL certificates |
| [URLScan.io](https://urlscan.io) | Website Screenshot Service | Searches indexed scans by domain |

Each discovered subdomain is cross-referenced against the source that identified it. Deduplication is applied across all sources.

### DNS Record Queries
Performs standard DNS resolution using `dnspython` to retrieve:
- **A / AAAA** — IPv4 and IPv6 address records
- **MX** — Mail exchange servers with priority
- **TXT** — Arbitrary text records (commonly SPF, DKIM, DMARC)
- **NS** — Authoritative name servers
- **CNAME** — Canonical name aliases
- **SOA** — Start of authority (primary NS, admin contact, serial)
- **SRV** — Service-specific records
- **CAA** — Certification authority authorization

Resolver timeouts and error handling are configured to prevent indefinite blocking on unresponsive name servers.

### SSL / TLS Certificate Inspection
Connects to a target across common TLS-enabled ports (443, 8443, 465, 993, 995, 2525, 587) and retrieves the peer certificate. Extracted fields include:
- **Subject** — Common name (CN) and organization (O)
- **Issuer** — Certificate authority that signed the certificate
- **Subject Alternative Names (SANs)** — All DNS names covered by the certificate
- **Validity Window** — Not-before and not-after timestamps
- **Remaining Days** — Time until expiration
- **Signature Algorithm** — Cryptographic algorithm used for signing
- **Serial Number** — Unique identifier

Certificate analysis is performed using the `cryptography` library's X.509 parser.

### Email Harvester
Discovers email addresses associated with a target domain by:
1. Scraping common web paths (`/contact`, `/about`, `/team`, `/privacy`, etc.) for email patterns
2. Parsing `/sitemap.xml` and `/sitemap_index.xml` to discover additional pages
3. Filtering discovered emails to ensure they match the target domain

Extraction uses regex-based email pattern matching and is rate-limited to prevent aggressive fetching.

### Google Dorking
Provides a catalog of 60+ pre-built Google search queries organized into 10 categories (admin panels, exposed files, directories, error messages, login pages, etc.). Each dork opens a new browser tab to the Google search results for manual review.

### GitHub Dorking
Catalogues code-search dorks targeting secrets, API keys, tokens, configuration files, and credential patterns across GitHub's public repositories.

### Browser Search Automation
Offers one-click search launching across 12 search engines simultaneously: Google, Bing, DuckDuckGo, Yahoo, Yandex, Baidu, Ask, AOL, Startpage, Qwant, Shodan, and GitHub. Useful for rapid manual OSINT triage.

### Reporting
Generates structured reports containing all collected intelligence for a target:
- **HTML** — Rendered template suitable for in-browser viewing
- **JSON** — Machine-readable export for integration with other tools
- **PDF** — Dark-themed styled document built with ReportLab

Reports capture subdomain lists, DNS records, and saved dorks. Each report is timestamped and linked to the originating target.

---

## Architecture

```
reconhub/
├── manage.py                 # Django management entry point
├── server.py                 # ASGI server bootstrap + auto-admin creation
├── requirements.txt          # Python package dependencies
├── reconhub/                 # Django project configuration
│   ├── settings.py           # App registry, middleware, DB, static config
│   └── urls.py               # Central route table (/api/*)
├── core/                     # Shared infrastructure
│   ├── models.py             # ActivityLog — audit trail for user actions
│   ├── middleware.py         # Request logging middleware
│   ├── utils.py              # Domain sanitization, truncation helpers
│   └── context_processors.py # Sidebar data injection
├── users/                    # Authentication & user management
│   ├── models.py             # Profile, UserSettings models
│   ├── views.py              # Registration, login, password reset
│   └── urls.py               # Auth route definitions
├── targets/                  # Target entity management
│   ├── models.py             # Target, Tag, TargetNote, SearchHistory
│   ├── views.py              # CRUD, favorites, notes, search history
│   └── urls.py               # Target route definitions
├── dorking/                  # Search engine dorking suite
│   ├── models.py             # DorkQuery persistence
│   ├── services.py           # Catalog definitions (60+ Google, GitHub dorks)
│   ├── dork_catalogs.py      # Dork categorization data
│   ├── views.py              # Dork browsing, saving, browser search
│   └── urls.py               # Dorking route definitions
├── recon/                    # Core reconnaissance engine
│   ├── models.py             # Subdomain, DNSRecord, SSLCertificate, EmailResult
│   ├── services.py           # All passive recon logic (subdomain, DNS, SSL, email)
│   ├── views.py              # Result display, run triggers, exports
│   └── urls.py               # Recon route definitions
├── reporting/                # Reporting engine
│   ├── models.py             # Report model with JSON data snapshots
│   ├── views.py              # Generate, list, detail, export endpoints
│   ├── pdf_export.py         # ReportLab PDF builder with custom dark theme
│   └── urls.py               # Reporting route definitions
├── dashboard/                # Home page & global search
│   ├── views.py              # Stats aggregation, search across entities
│   └── urls.py               # Dashboard route definitions
├── templates/                # Django template hierarchy
│   ├── auth/                 # Login, register, password reset templates
│   ├── dashboard/            # Home, search, activity feed templates
│   ├── dorking/              # Dork browser, saved dorks templates
│   ├── recon/                # Subdomain, DNS, SSL, email result templates
│   ├── reporting/            # Report list, detail, export templates
│   ├── targets/              # Target CRUD, detail templates
│   ├── users/                # Profile, settings templates
│   └── partials/             # Sidebar, topbar, messages, footer
└── static/                   # Compiled frontend assets
    ├── css/main.css          # Dark cyberpunk theme (1240+ lines)
    └── js/main.js            # Toast notifications, shortcuts, clipboard
```

### Data Flow

1. **User** adds a target domain and selects a recon module
2. **View layer** validates permissions, delegates to the service layer
3. **Service layer** queries external public APIs/sources using HTTP(S) or DNS
4. **Raw responses** are parsed and normalized into structured dictionaries
5. **Model layer** persists results to SQLite with deduplication
6. **View layer** passes results to templates for rendering
7. **User** reviews results in-browser or exports via the reporting module

All external requests use a shared, connection-pooled `requests.Session` with retry logic and timeouts to handle transient failures gracefully.

---

## Security Model

- **Zero active scanning** — No packets are sent to target infrastructure
- **Local-first** — All data resides in a local SQLite database; no external telemetry
- **Authentication required** — All routes are gated by Django's `@login_required`
- **CSRF protection** — Enabled globally for all state-changing operations
- **User isolation** — Data is scoped to authenticated users via `filter(user=request.user)`

---

## Dependencies

| Package | Role |
|---------|------|
| Django 5.0 | Web framework (ORM, auth, routing, templates) |
| WhiteNoise | Static file serving in production |
| dnspython | DNS resolution for record queries |
| BeautifulSoup4 | HTML parsing for email harvesting |
| ReportLab | PDF generation with custom styling |
| Pillow | Image support (ReportLab dependency) |
| cryptography | X.509 certificate parsing |
| requests | HTTP client with connection pooling and retry |
| uvicorn | ASGI server for production deployment |

---

## Installation

```bash
# Clone and enter the project directory
# Create a virtual environment
python3 -m venv .venv && source .venv/bin/activate
# On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python manage.py migrate

# Collect static assets
python manage.py collectstatic --noinput

# Start the development server
python manage.py runserver 0.0.0.0:8000

# Or for production via ASGI:
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 2
```

The application will automatically create an admin superuser on first startup if one does not exist.

### Default Credentials
| Field | Value |
|-------|-------|
| Username | `arkani` |
| Password | `python123` |


---

## Use Cases

- **Bug Bounty Reconnaissance** — Passive subdomain discovery and certificate analysis for scope mapping
- **OSINT Investigations** — Domain intelligence gathering for threat intelligence and research
- **Security Assessments** — Pre-engagement reconnaissance to understand a target's digital footprint
- **Educational Training** — Demonstrating passive recon techniques in controlled environments

---

## License

For educational and authorized security testing purposes only. Users are responsible for compliance with applicable laws and target scope restrictions.
