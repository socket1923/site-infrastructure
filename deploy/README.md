# Restricted production deployment

The release workflow builds a multi-architecture image on a GitHub-hosted runner, pushes an immutable digest to GHCR, and optionally invokes a dedicated self-hosted deployment runner. The runner does not hold a normal node11 shell key: node11 must restrict the key to `node11-ssh-dispatch`, which accepts only a digest under `ghcr.io/socket1923/site-infrastructure`.

Production deployment remains disabled until all prerequisites are verified.

## Prerequisites

1. Inspect the six-node Swarm and confirm the routing mesh can publish TCP/443 on node11 while tasks run on at least two nodes.
2. Confirm Sophos forwards the public origin flow to node11 TCP/443 and restricts origin access to intended sources.
3. Create versioned Swarm secrets from the existing origin certificate and private key. Do not commit or upload certificate material.
4. Perform the first stack migration manually with an immutable image digest and verify both replicas.
5. Install the dispatch and deploy scripts on node11 as root-owned, non-writable files.
6. Configure a dedicated deployment account, source-restricted key, disabled forwarding/PTY, and exact sudo rule.
7. Register a dedicated, disposable self-hosted runner with labels `self-hosted`, `linux`, and `socket23-deploy`. Do not run pull-request jobs on it.
8. Install `deploy/runner-trigger` as `/usr/local/bin/socket23-trigger-deploy` on the runner and configure its `node11-deploy` SSH alias with a pinned host key.
9. Make the GHCR package publicly readable or configure a narrowly scoped read-only registry credential on the Swarm.
10. Protect `master`, require the `CI / validate` check, and disallow force pushes.
11. Set repository variable `ENABLE_PRODUCTION_DEPLOY=true` only after a rollback test passes.

## Swarm secrets

Use versioned names so certificate rotation is explicit:

```bash
docker secret create socket23_tls_fullchain_YYYYMMDD /path/to/fullchain.pem
docker secret create socket23_tls_privkey_YYYYMMDD /path/to/privkey.pem
```

Deploy the initial stack with an immutable digest:

```bash
export IMAGE_REF='ghcr.io/socket1923/site-infrastructure@sha256:<64-hex-digest>'
export TLS_FULLCHAIN_SECRET='socket23_tls_fullchain_YYYYMMDD'
export TLS_PRIVKEY_SECRET='socket23_tls_privkey_YYYYMMDD'
docker stack deploy --prune -c static-site/stack.yaml web
```

## Restricted node11 account

Install scripts:

```bash
install -o root -g root -m 0755 deploy/node11-ssh-dispatch /usr/local/sbin/socket23-ssh-dispatch
install -o root -g root -m 0755 deploy/node11-deploy /usr/local/sbin/socket23-deploy
```

The deployment account must not receive an unrestricted key. Its `authorized_keys` entry should use all of:

```text
from="<runner-IP>/32",restrict,command="/usr/local/sbin/socket23-ssh-dispatch" ssh-ed25519 <DEPLOY-PUBLIC-KEY> socket23-deploy
```

An sshd `Match User` block should disable passwords, keyboard-interactive auth, forwarding, and TTY allocation. The sudo rule should permit only `/usr/local/sbin/socket23-deploy` for this account. Validate with `sshd -t` and `sshd -T -C ...` before reloading.

Runner trigger script:

```bash
#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-}" =~ ^ghcr\.io/socket1923/site-infrastructure@sha256:[0-9a-f]{64}$ ]]
exec ssh -o BatchMode=yes -o IdentitiesOnly=yes -o StrictHostKeyChecking=yes   node11-deploy "deploy $1"
```

## Rollback

The Swarm update policy uses automatic rollback. The restricted deploy script also rolls back if the expected replicas do not become healthy or the local HTTPS smoke test fails. Keep the previous digest available in GHCR and exercise rollback before enabling unattended production deployment.
