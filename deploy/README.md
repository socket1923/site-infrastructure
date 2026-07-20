# Pull-based production deployment

The safe delivery path is outbound-only:

```text
protected master -> GitHub-hosted build -> public GHCR image
                                             |
                                             v
                                   node11 pull timer
                                             |
                                             v
                              digest-pinned Swarm update
```

GitHub never receives a node11 SSH key and no inbound deployment listener is exposed. The node timer pulls the public `latest` tag, resolves it to an immutable approved digest, compares it with the running service, updates one replica at a time, verifies replica health and local HTTPS, and rolls back on failure.

## Verified environment assumptions

- The live Swarm currently contains one ARMv7 manager node.
- Two replicas therefore provide process/update continuity, not node-level high availability.
- Swarm ingress publishes TCP/80 and TCP/443 once while both replicas use internal ports 8080 and 8443.
- The pull agent refuses to touch the legacy service until the stack has label `com.socket23.delivery=immutable-pull-v1`.

## One-time migration

1. Merge only after CI is green.
2. Let `Build and publish` create `ghcr.io/socket1923/site-infrastructure:latest` for AMD64 and ARMv7.
3. Make the GHCR package publicly readable.
4. Back up the current service spec and certificate metadata.
5. Create versioned Swarm secrets without printing certificate material:

```bash
docker secret create socket23_tls_fullchain_YYYYMMDD /etc/ssl/socket23/fullchain.pem
docker secret create socket23_tls_privkey_YYYYMMDD /etc/ssl/socket23/privkey.pem
```

6. Resolve `latest` to an immutable digest on node11 and deploy the initial stack:

```bash
docker pull ghcr.io/socket1923/site-infrastructure:latest
export IMAGE_REF="$(docker image inspect   --format '{{range .RepoDigests}}{{println .}}{{end}}'   ghcr.io/socket1923/site-infrastructure:latest   | grep '^ghcr.io/socket1923/site-infrastructure@sha256:'   | head -n 1)"
export TLS_FULLCHAIN_SECRET=socket23_tls_fullchain_YYYYMMDD
export TLS_PRIVKEY_SECRET=socket23_tls_privkey_YYYYMMDD
docker stack deploy --prune -c static-site/stack.yaml web
```

7. Verify two healthy replicas, local HTTP redirect, local HTTPS, and the public Cloudflare route.
8. Exercise one controlled bad-image rollback before enabling the timer.

## Preferred timer installation

Install the root-owned fixed script and units:

```bash
sudo install -o root -g root -m 0755 deploy/node11-pull-deploy /usr/local/sbin/socket23-pull-deploy
sudo install -o root -g root -m 0644 deploy/socket23-pull-deploy.service /etc/systemd/system/socket23-pull-deploy.service
sudo install -o root -g root -m 0644 deploy/socket23-pull-deploy.timer /etc/systemd/system/socket23-pull-deploy.timer
sudo systemctl daemon-reload
sudo systemctl enable --now socket23-pull-deploy.timer
```

Validate:

```bash
sudo systemctl start socket23-pull-deploy.service
sudo systemctl status socket23-pull-deploy.service --no-pager
sudo journalctl -u socket23-pull-deploy.service --no-pager -n 100
docker service ps web_web
```

The current `analyst` account is in the `docker` group, which is root-equivalent. After the root-owned pull timer is installed and verified, remove routine CI/CD dependence on unrestricted analyst SSH and consider replacing it with a narrower audit identity.

## Firewall requirement

Node11 logs show arbitrary Internet scanners reaching the origin directly. Sophos should restrict WAN-to-origin TCP/80 and TCP/443 to current Cloudflare source ranges, while retaining explicit internal-management access. Only trust `CF-Connecting-IP` after that source restriction is enforced and tested.

## Rollback

The stack update policy and pull script both invoke Swarm rollback. The previous digest remains available in GHCR. Manual rollback:

```bash
docker service rollback --detach=false web_web
docker service ps web_web
curl -k --resolve socket23.com:443:127.0.0.1 https://socket23.com/
```
