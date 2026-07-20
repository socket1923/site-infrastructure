# Security review

Review date: 2026-07-20

## Executive result

The public site is currently reachable through Cloudflare and the node11 HTTPS origin returns the same content. The repository had no CI workflow, no branch protection, manual mutable-`latest` deployments, an ineffective Dockerfile, root container execution, host bind mounts, and a single-replica stop-first Swarm update policy. Live inspection found that node11 had recently restarted after an unclean shutdown: the previous Swarm task exited 255 and systemd-journald replaced a corrupted journal. Because this is a one-node Swarm, that restart is the strongest available explanation for the Cloudflare 522 window.

No repository secrets were detected by Gitleaks. The live response has strong baseline security headers.

A passive OWASP ZAP baseline crawled 27 live URLs and reported **0 failures**, 56 passes, and 11 warnings. The warnings were primarily missing inherited headers on static assets, long-lived cache behavior, `style-src 'unsafe-inline'`, Cloudflare-injected `/cdn-cgi/` assets, and the public message form that existed during the review. Header inheritance and cache revalidation were fixed in the hardening release. The personal-portfolio release removes the form and its external processor, sets `form-action 'none'`, confirms the rewritten pages have no inline style attributes, and removes `unsafe-inline` from `style-src`.

## Findings addressed by this branch

### High — build did not represent production

`Dockerfile` copied a full top-level NGINX configuration into `conf.d`, where directives such as `user`, `events`, and `http` are invalid. Production bypassed the image entirely by bind-mounting site and configuration files into `nginx:alpine`. Code changes therefore did not follow a reliable immutable-image path.

**Fix:** build one digest-pinned, multi-architecture, non-root image containing the configuration and site.

### High — root container and mutable base image

Trivy reported `DS-0002`: no non-root `USER`. Both the base and production service used mutable Alpine tags.

**Fix:** use the ARMv7-capable `nginx-unprivileged` image pinned by multi-architecture digest, explicitly run as UID/GID 101, drop all capabilities, enforce `no-new-privileges`, use a read-only root filesystem, and retain resource limits.

### High — deployment could create outages and drift

The service used one replica, host-mode port 443, `stop-first`, relative host bind mounts, and manual `latest` updates. A task reschedule could fail when files were absent on another node, while an update intentionally removed the only origin before starting its replacement.

**Fix:** prepare two same-node replicas behind Swarm ingress, immutable image digests, start-first updates, health monitoring, automatic rollback, and no site/config bind mounts. This prevents update-time gaps but does not provide node-level high availability; a second Swarm node or independent failover origin remains future work.

### High — no CI/CD controls

The public repository had no Actions workflows and `master` was unprotected.

**Fix:** add dependency-free site validation, Compose/Swarm validation, Gitleaks, non-root/read-only HTTPS smoke tests, Trivy image scanning, and ARMv7 multi-architecture build verification. The release workflow publishes digest-addressed images with SBOM and provenance. Node11 uses a fixed outbound pull agent, so GitHub receives no production SSH key and no inbound deployment listener is exposed.

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

### High — origin exposed directly to arbitrary Internet clients

Live NGINX logs contain requests whose TCP peers are neither Cloudflare nor internal management addresses, including generic Internet scanners. Sophos is therefore forwarding the origin without a Cloudflare-only source restriction. This permits bypass of Cloudflare controls and makes `CF-Connecting-IP` unsafe to trust globally.

**Status:** open at the firewall. Restrict WAN-to-node11 TCP/80 and TCP/443 to current Cloudflare address ranges, retain a separate explicit internal-management rule, then verify both allowed Cloudflare traffic and denied direct-origin traffic.

### Medium — stale and contradictory operations documentation

Documentation described IPFire/HAProxy and port 8080 while the current origin listens only on 443. Manual recovery instructions included service removal and mutable images.

**Fix:** remove the obsolete deployment and form guides, replace the top-level README with the current pull-based architecture, and keep the detailed migration and rollback design under `deploy/README.md`.

### Low — deprecated browser header

The prior configuration set `X-XSS-Protection: 1; mode=block`, which is obsolete and has caused browser-side issues historically.

**Fix:** explicitly disable the legacy filter with `X-XSS-Protection: 0`; CSP remains the primary XSS control.

## Node11 staging verification

The exact stack was deployed on isolated ports 8081/8444 using the ARMv7 artifact. Two replicas reached healthy state with UID/GID 101, read-only root filesystems, all capabilities dropped, TLS secret mode `0400`, and `no-new-privileges=true` verified on both runtime containers. The staged homepage hash matched the branch checkout. An intentional failed update reached `rollback_completed`, restored both healthy replicas, and retained valid HTTPS. A simultaneous corrected public probe completed 120/120 requests with zero failures.

This exercise caught two engine-specific issues before production: node11 silently discards Compose tmpfs and `security_opt` settings during `docker stack deploy`. The image now keeps runtime state under Docker's built-in `/dev/shm`; a scoped service-API helper applies and verifies `NoNewPrivileges` after initial stack deployment.

## Remaining infrastructure verification

Before enabling deployment:

- add true node-level redundancy if availability beyond rolling updates is required;
- replace unrestricted deployment access with the fixed outbound pull timer;
- confirm Sophos DNAT/load-balancer targets and logs for prior Cloudflare 522 windows;
- verify Cloudflare SSL mode is Full (strict);
- verify whether origin TCP/443 is limited to Cloudflare or another intentional proxy path;
- install and verify the fixed root-owned outbound pull timer after the initial migration;
- enable branch protection only after the new CI check is registered and green.
