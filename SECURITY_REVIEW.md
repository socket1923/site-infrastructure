# Security review

Review date: 2026-07-20

## Executive result

The public site is currently reachable through Cloudflare and the node11 HTTPS origin returns the same content. The repository had no CI workflow, no branch protection, manual mutable-`latest` deployments, an ineffective Dockerfile, root container execution, host bind mounts, and a single-replica stop-first Swarm update policy. Those deployment weaknesses can create an origin gap long enough for Cloudflare to return 522 during image pulls, restarts, or node disruption.

No repository secrets were detected by Gitleaks. The live response has strong baseline security headers.

A passive OWASP ZAP baseline crawled 27 live URLs and reported **0 failures**, 56 passes, and 11 warnings. The warnings were primarily missing inherited headers on static assets, long-lived cache behavior, `style-src 'unsafe-inline'`, Cloudflare-injected `/cdn-cgi/` assets, and a generic anti-CSRF warning on the third-party Formspree contact form. This branch fixes header inheritance and replaces one-year immutable caching on unversioned CSS/JS with five-minute revalidation. Eliminating `unsafe-inline` requires a separate HTML/CSS refactor.

## Findings addressed by this branch

### High — build did not represent production

`Dockerfile` copied a full top-level NGINX configuration into `conf.d`, where directives such as `user`, `events`, and `http` are invalid. Production bypassed the image entirely by bind-mounting site and configuration files into `nginx:alpine`. Code changes therefore did not follow a reliable immutable-image path.

**Fix:** build one digest-pinned, multi-architecture, non-root image containing the configuration and site.

### High — root container and mutable base image

Trivy reported `DS-0002`: no non-root `USER`. Both the base and production service used mutable Alpine tags.

**Fix:** use the ARMv7-capable `nginx-unprivileged` image pinned by multi-architecture digest, explicitly run as UID/GID 101, drop all capabilities, enforce `no-new-privileges`, use a read-only root filesystem, and retain resource limits.

### High — deployment could create outages and drift

The service used one replica, host-mode port 443, `stop-first`, relative host bind mounts, and manual `latest` updates. A task reschedule could fail when files were absent on another node, while an update intentionally removed the only origin before starting its replacement.

**Fix:** prepare a two-replica routing-mesh stack, immutable image digests, start-first updates, health monitoring, automatic rollback, and no site/config bind mounts. This stack must not be applied until the live Swarm and Sophos path are inspected.

### High — no CI/CD controls

The public repository had no Actions workflows and `master` was unprotected.

**Fix:** add dependency-free site validation, Compose/Swarm validation, Gitleaks, non-root/read-only HTTPS smoke tests, Trivy image scanning, and ARMv7 multi-architecture build verification. The release workflow publishes digest-addressed images with SBOM and provenance. Production deployment is disabled by default and requires a dedicated restricted runner path.

### Medium — TLS private key exposed as host bind mount

The production service bind-mounted `/etc/ssl/socket23`, increasing coupling to host paths and making scheduling/permission behavior implicit.

**Fix:** define external Swarm secrets with explicit target names and ownership. Certificate rotation remains a separate reviewed operation.

### Medium — CSP/privacy conflict in project page

The project page loaded a third-party GitHub statistics image while CSP allowed images only from the same origin. Its inline `onerror` handler was also blocked by `script-src 'self'`. This leaked visitor metadata when relaxed and did not work under the declared policy.

**Fix:** remove the remote image and inline handler; use a normal privacy-preserving profile link.

### Medium — unversioned assets cached for one year

The existing configuration marked `styles.css` and `scripts.js` immutable for one year even though their filenames are reused. Browsers could therefore keep old code after a successful deployment.

**Fix:** apply a one-time URL version bump in the HTML and reduce CSS/JS caching to five minutes with revalidation. HTML now uses `no-cache` so deployments become visible without a hard refresh.

### Medium — rate limiting does not establish the real client IP

The NGINX rate key is the TCP peer. Behind Cloudflare/Sophos this can group many visitors under proxy addresses, causing collateral 429 responses. Blindly trusting `CF-Connecting-IP` would permit spoofing if the origin is reachable from non-Cloudflare sources.

**Status:** open. First verify Sophos permits origin traffic only from intended proxies, then configure and maintain trusted proxy ranges before changing the rate key.

### Medium — stale and contradictory operations documentation

Documentation described IPFire/HAProxy and port 8080 while the current origin listens only on 443. Manual recovery instructions included service removal and mutable images.

**Status:** partially addressed by the new restricted deployment documentation. Rewrite the general architecture section after the live Sophos and Swarm inspection.

### Low — deprecated browser header

The prior configuration set `X-XSS-Protection: 1; mode=block`, which is obsolete and has caused browser-side issues historically.

**Fix:** explicitly disable the legacy filter with `X-XSS-Protection: 0`; CSP remains the primary XSS control.

## Remaining infrastructure verification

Before enabling deployment:

- inspect all Swarm nodes, managers, labels, availability, and Docker versions;
- verify node11 SSH authorization and install a forced-command deployment identity;
- confirm Sophos DNAT/load-balancer targets and logs for prior Cloudflare 522 windows;
- verify Cloudflare SSL mode is Full (strict);
- verify whether origin TCP/443 is limited to Cloudflare or another intentional proxy path;
- run a controlled rolling update and rollback while continuously probing externally;
- enable branch protection only after the new CI check is registered and green.
