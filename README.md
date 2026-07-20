# Socket23 site infrastructure

This repository contains the static site and secure delivery path for [socket23.com](https://socket23.com), Joseph Miller’s personal technical portfolio.

Socket23 is Joseph’s personal lab and publishing handle. The site is organized around his experience, successful projects, lab work, and technical notes.

## Site map

- `/` — personal introduction and successful work
- `/projects.html` — detailed project summaries
- `/experience.html` — systems experience across the stack
- `/about.html` — background, working style, and what Socket23 means
- `/lab.html` — infrastructure, security, and private-AI lab
- `/blog.html` — technical notes and writing queue
- `/contact.html` — links to LinkedIn, GitHub, and Credly
- `/work/*.html` — eight detailed, first-person case studies
- `/sitemap.xml` and `/robots.txt` — public discovery metadata

The former services, testimonials, collaboration, community, and team routes return permanent redirects into the personal portfolio.

## Delivery architecture

```text
protected pull request
        |
        v
GitHub Actions validation
        |
        v
multi-architecture image published to GHCR
        |
        v
node11 outbound pull process
        |
        v
digest-pinned Docker Swarm update
        |
        v
runtime and HTTPS verification or automatic rollback
```

GitHub does not hold a production SSH key. Production pulls the public image, resolves the mutable tracking tag to an immutable digest, and updates the Swarm service only after the repository’s migration and runtime-security markers are present.

## Runtime controls

- Unprivileged NGINX image
- UID/GID 101
- Read-only root filesystem
- Linux capabilities dropped
- `no-new-privileges`
- TLS certificate and private key supplied as Swarm secrets
- Private-key mode `0400`
- Two same-node replicas
- Start-first updates
- Health checks and automatic rollback
- Bounded CPU and memory
- Rate limiting and request-size limits
- Security headers on normal and error responses
- No backend, database, account system, tracking, analytics, cookies, uploads, or public form

Two replicas protect normal rolling updates and process failure. They do not provide node-level availability because the current Swarm has one active node.

## Browser security policy

The site uses a restrictive Content Security Policy:

- scripts, styles, images, and connections are restricted to the site
- public form submission is prohibited with `form-action 'none'`
- framing and plugins are blocked
- mixed content is upgraded
- cross-origin isolation headers are enabled
- HSTS is enabled for the domain

Inline JavaScript and inline event handlers are rejected by the static validator. External links opened in a new tab must include `rel="noopener noreferrer"`.

## Repository layout

```text
.
├── .github/workflows/       # protected validation and release workflows
├── deploy/                  # pull deployment, migration, and rollback helpers
├── scripts/                 # static validation and runtime smoke tests
├── PROJECT_INVENTORY.md     # confirmed, privacy-safe source material for portfolio content
├── static-site/
│   ├── Dockerfile           # digest-pinned unprivileged NGINX image
│   ├── nginx.conf           # TLS, headers, limits, redirects, and static routing
│   ├── compose.yaml         # local runtime definition
│   ├── stack.yaml           # production Swarm definition
│   └── site/                # HTML, CSS, and minimal navigation JavaScript
├── SECURITY_REVIEW.md       # recorded security findings and verification
└── README.md
```

## Local verification

From the repository root:

```bash
python3 scripts/validate_site.py
cd static-site
make config
cd ..
scripts/smoke-test.sh socket23-site:local
```

The validator checks local links, canonical URLs, the sitemap, case-study structure, person-first identity rules, insecure URLs, inline scripts, inline event handlers, form prohibition, CSP compatibility, and tabnabbing controls.

The smoke test builds and runs the same hardened container shape used by production and verifies:

- HTTP-to-HTTPS redirect
- HTTPS response
- personal homepage and detailed case-study markers
- sitemap and robots discovery files
- security headers
- static-asset cache policy
- custom 404 response
- non-root execution
- read-only root filesystem

## Protected release workflow

Changes should go through a branch and pull request:

```bash
git switch -c content/my-change
# edit static-site/site/
python3 scripts/validate_site.py
git add static-site/site
git commit -m "Describe the change"
git push -u origin HEAD
gh pr create --fill
```

The required validation job includes:

- static site checks
- Compose and Swarm rendering
- Actionlint and ShellCheck
- Gitleaks
- AMD64 runtime smoke test
- Trivy image scan
- AMD64 and ARMv7 build verification

After a protected merge, the release workflow publishes AMD64 and ARMv7 images with SBOM and provenance. Node11 normally adopts the approved digest within two minutes. See [deploy/README.md](deploy/README.md) for the deployment and rollback design.

## Privacy

The site intentionally does not publish a personal email address or phone number. It does not collect visitor data. The Connect page points to Joseph’s public professional profiles:

- [GitHub](https://github.com/socket23)
- [LinkedIn](https://www.linkedin.com/in/joseph-miller-cybersecurity)
- [Credly](https://www.credly.com/users/josephamiller)

Do not publish credentials, private keys, internal addresses, sensitive logs, diagnostic bundles, private infrastructure diagrams, or identifiable production details in this repository.

## License and reuse

The infrastructure patterns are published for learning and adaptation. Personal biography, project narratives, and branding remain Joseph Miller’s content.
