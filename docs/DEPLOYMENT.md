# Deployment, access and recovery

Updated 30 September 2026. The application runs locally and in a tested Docker image. Public hosting, DNS and an institutional security approval are not provisioned by this repository. Use synthetic records throughout a public demonstration.

## Run on this computer

```bash
python3 server.py --port 8046
```

Open `http://127.0.0.1:8046`. The optional demonstration roles use `Demo#26046`. Records persist in `data/ctms.sqlite`; a restart invalidates sessions but preserves records. The standard-library listener is for local development. The container uses Waitress for application serving.

## Named accounts

The administrator opens **Access management**, creates a named account, chooses its role and study assignments, and supplies a temporary password of 12–128 characters. First sign-in requires a replacement password. Non-administrators with no assignments see no study records. An administrator can change assignments, disable an account, reset its password or revoke sessions. These operations invalidate previous sessions. The last active named administrator cannot be disabled or demoted.

Passwords are salted and derived using PBKDF2-HMAC-SHA256 with 600,000 iterations. Password hashes are omitted from API responses and audit records. Named-account authentication does not establish professional credentials, institutional delegation, MFA or a validated electronic signature.

For a fresh installation with demonstration login disabled, set `CTMS_ADMIN_USERNAME` and a private `CTMS_ADMIN_PASSWORD` before starting. Bootstrap creates the initial administrator only when no accounts exist. Remove the bootstrap secret from the host configuration after the account is provisioned and its password changed; changing that environment value does not reset an existing account.

## Container rehearsal

```bash
docker build -t anvaya-ctms:local .
docker run --rm -p 127.0.0.1:8046:8046 \
  --mount type=volume,src=anvaya-demo-data,dst=/app/data \
  anvaya-ctms:local
```

Stop the existing local service first if it already owns port 8046, or bind another host port. This command enables the default synthetic demonstration login. It is not the HTTPS deployment. The container runs as UID 10001, stores data in `/app/data`, and uses one Waitress process with eight worker threads. The application serialises database work; it has no measured multi-site capacity claim. Multiple replicas are unsupported because sessions and the write lock are process-local.

## Public HTTPS installation

Use one institution-approved host with Docker Compose, persistent storage and a DNS name pointing to it. The included deployment is deliberately one application instance. A hosting account, domain and spending authority must exist before provisioning a paid service.

1. Copy this source to the host. Keep the production database, terminology packages and secrets out of public repositories and submission ZIPs.
2. Copy `.env.example` to `.env`. Set `ANVAYA_DOMAIN` to the real DNS hostname and replace the bootstrap password with a private, unique value. Do not reuse a password shown in a test or presentation.
3. Keep `CTMS_DEMO_LOGIN=false` for named access. A deliberately public synthetic role demonstration may enable it; every visitor can then choose the demonstration administrator role and change synthetic data.
4. Run `docker compose --env-file .env config --quiet`, then `docker compose up -d --build`.
5. Allow inbound TCP 80/443, with UDP 443 optional. Caddy provisions HTTPS when public DNS and certificate-authority reachability are correct. The application port is not published.
6. Sign in with the bootstrap account, replace its password, create the authorised reviewer accounts and remove the bootstrap secret from the host configuration.
7. Check `/api/health`, sign-out behaviour, Secure/HttpOnly/SameSite cookies, assigned-study restrictions, source-file rejection, exports and an actual restore rehearsal before sharing the URL.

The proxy occupies `172.30.46.2` on the isolated backend network. Waitress accepts forwarded client address/protocol headers only from that address; this prevents all users sharing the proxy's login-throttling identity. If the subnet conflicts with the host network, change the Compose subnet/proxy address and the Dockerfile's `--trusted-proxy` value together. Keep the backend isolated and never configure arbitrary client headers as trusted.

The HTTPS configuration has been syntax-validated in Caddy. Separately, the synthetic demonstration is publicly reachable through Render at [anvaya-2026-ctms.onrender.com](https://anvaya-2026-ctms.onrender.com); [anvaya-2026.vercel.app](https://anvaya-2026.vercel.app) is a static entry page that opens that service. Render terminates HTTPS for this demo. [Waitress reverse-proxy guidance](https://docs.pylonsproject.org/projects/waitress/en/stable/reverse-proxy.html) and [Caddy automatic HTTPS](https://caddyserver.com/docs/automatic-https) describe the self-hosted deployment mechanisms.

The public free-tier deployment uses one Waitress process and an ephemeral SQLite file. It can reset on deploy or host replacement and is only for synthetic demonstration data. Institutional use still requires persistent encrypted storage, named access with shared demo login disabled, backups, monitoring, recovery testing and security/privacy acceptance.

## Configuration reference

| Variable | Purpose |
|---|---|
| `CTMS_DB` | SQLite path; default `data/ctms.sqlite` locally and `/app/data/ctms.sqlite` in Docker |
| `CTMS_DEMO_LOGIN` | `true` enables shared synthetic personas; Compose defaults to `false` |
| `CTMS_DEMO_PASSWORD` | Optional shared demo password override; update the displayed demo hint if using this |
| `CTMS_ADMIN_USERNAME` | Initial named administrator username when bootstrapping an empty account table |
| `CTMS_ADMIN_PASSWORD` | Private bootstrap password, minimum 12 characters; used only for initial account creation |
| `CTMS_SECURE_COOKIE` | `true` sends Secure session cookies; Compose enables it behind HTTPS |
| `ANVAYA_DOMAIN` | Public DNS hostname used by Caddy |
| `PORT` | Local `server.py` listener port when `--port` is absent |

`/api/health` confirms a database read and exposes no study details. Configure host monitoring to poll it and alert an operator; the repository does not send alerts to an external destination. Container health checks run every 30 seconds.

## Back up and restore

```bash
mkdir -p backups
python3 ops.py backup backups/clinical-2026-09-30.sqlite
python3 ops.py verify backups/clinical-2026-09-30.sqlite
python3 ops.py restore backups/clinical-2026-09-30.sqlite data/restored-review.sqlite
CTMS_DB=data/restored-review.sqlite python3 server.py --port 8047
```

Backups use SQLite's online backup API, including committed WAL data. They verify SQLite integrity and the stored audit hash chain. Destinations must be new: existing files and recovery sidecars are never overwritten. The output is created with owner-only permissions. Restoration creates a new database; it does not replace or switch a running application.

The database includes document bodies, account hashes, source lineage and any supplied dictionary packages. Protect backups as carefully as the application data. Permission mode 0600 is not encryption. Institutional operations need encrypted backup storage, authorised key access, retention policy, automated scheduling, failure alerts and recurring restore exercises. Preserve any required independently retained audit checkpoints; a hash chain cannot authenticate itself against an operator who rewrites every record.

For the live local upgrade, `backups/pre-end-to-end-upgrade.sqlite` was created and verified before restart. That local backup is excluded from Git, the Docker build and submission packaging.

## Release checks and rollback

Install `requirements.txt` and `requirements-dev.txt` in a virtual environment, then run:

```bash
.venv/bin/python tests/run_checks.py --browser
```

The suite uses temporary databases. Chrome is required for the browser portion. The schema upgrade creates additional JSON-record tables without resetting existing records. Legacy studies retain their recorded protocol/consent fallback and do not receive invented historical approval dates.

Before an update, make a verified backup, record the image digest and preserve the previous image. If an update fails before accepting new writes, stop the service and inspect the failure before selecting the prior image/database. Once new writes exist, restoring an earlier database loses those writes unless they are reconciled. A rollback is an operator-controlled action, not an automatic reset.

## Institutional acceptance

Hosting is one part of release readiness. Institutional SSO/MFA, approved SOPs and delegation, authentic evidence, applicable DPDP obligations, CERT-In processes, protected logs, encryption, security review, terminology rights and partner acceptance remain governed activities. See [PRODUCTION_GAP_ANALYSIS.md](PRODUCTION_GAP_ANALYSIS.md). No cloud-compliance or clinical-system certification is implied by a successful Docker build.
