#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
IMAGE=${1:-socket23-site:test}
TMP=$(mktemp -d)
CID=""

cleanup() {
  if [[ -n "$CID" ]]; then
    docker rm -f "$CID" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP"
}
trap cleanup EXIT

openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout "$TMP/privkey.pem" \
  -out "$TMP/fullchain.pem" \
  -subj '/CN=socket23.com' \
  -addext 'subjectAltName=DNS:socket23.com' >/dev/null 2>&1
chmod 0444 "$TMP/fullchain.pem" "$TMP/privkey.pem"

docker build -t "$IMAGE" "$ROOT/static-site"

CID=$(docker run -d --rm \
  --user 101:101 \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --mount "type=bind,src=$TMP/fullchain.pem,dst=/run/secrets/tls_fullchain.pem,readonly" \
  --mount "type=bind,src=$TMP/privkey.pem,dst=/run/secrets/tls_privkey.pem,readonly" \
  -p 127.0.0.1::8080 \
  -p 127.0.0.1::8443 \
  "$IMAGE")

PORT=$(docker port "$CID" 8443/tcp | awk -F: 'NR==1 {print $NF}')
HTTP_PORT=$(docker port "$CID" 8080/tcp | awk -F: 'NR==1 {print $NF}')

for _ in $(seq 1 30); do
  if curl --silent --show-error --fail \
      --cacert "$TMP/fullchain.pem" \
      --resolve "socket23.com:$PORT:127.0.0.1" \
      "https://socket23.com:$PORT/" \
      -o "$TMP/index.html"; then
    break
  fi
  sleep 1
done

grep -q 'Socket23' "$TMP/index.html"
grep -q 'I make difficult systems work.' "$TMP/index.html"
grep -q 'Selected successful work' "$TMP/index.html"

curl --silent --show-error --fail \
  --cacert "$TMP/fullchain.pem" \
  --resolve "socket23.com:$PORT:127.0.0.1" \
  "https://socket23.com:$PORT/work/vmware-hyper-v-san-migration.html" \
  -o "$TMP/case-study.html"
grep -q 'How I validated it' "$TMP/case-study.html"
grep -q 'My role' "$TMP/case-study.html"

curl --silent --show-error --fail \
  --cacert "$TMP/fullchain.pem" \
  --resolve "socket23.com:$PORT:127.0.0.1" \
  "https://socket23.com:$PORT/sitemap.xml" \
  -o "$TMP/sitemap.xml"
grep -q 'work/local-ai-agent-platform.html' "$TMP/sitemap.xml"

curl --silent --show-error --fail \
  --cacert "$TMP/fullchain.pem" \
  --resolve "socket23.com:$PORT:127.0.0.1" \
  "https://socket23.com:$PORT/robots.txt" \
  -o "$TMP/robots.txt"
grep -q 'Sitemap: https://socket23.com/sitemap.xml' "$TMP/robots.txt"

HEADERS=$(curl --silent --show-error --fail \
  --cacert "$TMP/fullchain.pem" \
  --resolve "socket23.com:$PORT:127.0.0.1" \
  -D - -o /dev/null \
  "https://socket23.com:$PORT/")
grep -qi '^content-security-policy:' <<<"$HEADERS"
grep -qi "^content-security-policy:.*form-action 'none'" <<<"$HEADERS"
if grep -qi "^content-security-policy:.*unsafe-inline" <<<"$HEADERS"; then
  echo "CSP still permits unsafe-inline" >&2
  exit 1
fi
grep -qi '^strict-transport-security:' <<<"$HEADERS"
grep -qi '^x-content-type-options: nosniff' <<<"$HEADERS"
grep -qi '^cache-control: no-cache' <<<"$HEADERS"

CSS_HEADERS=$(curl --silent --show-error --fail \
  --cacert "$TMP/fullchain.pem" \
  --resolve "socket23.com:$PORT:127.0.0.1" \
  -D - -o /dev/null \
  "https://socket23.com:$PORT/styles.css")
grep -qi '^cache-control:.*max-age=300.*must-revalidate' <<<"$CSS_HEADERS"
grep -qi '^content-security-policy:' <<<"$CSS_HEADERS"

CODE=$(curl --silent --show-error \
  --cacert "$TMP/fullchain.pem" \
  --resolve "socket23.com:$PORT:127.0.0.1" \
  -o /dev/null -w '%{http_code}' \
  "https://socket23.com:$PORT/definitely-not-present")
[[ "$CODE" == "404" ]]

while read -r OLD NEW; do
  REDIRECT_HEADERS=$(curl --silent --show-error \
    --cacert "$TMP/fullchain.pem" \
    --resolve "socket23.com:$PORT:127.0.0.1" \
    -D - -o /dev/null \
    "https://socket23.com:$PORT$OLD")
  grep -qE '^HTTP/[0-9.]+ 301' <<<"$REDIRECT_HEADERS"
  grep -qi "^location: $NEW" <<<"$REDIRECT_HEADERS"
done <<'REDIRECTS'
/services.html /experience.html
/testimonials.html /projects.html
/collaboration.html /contact.html
/community.html /lab.html
/team/joseph-miller.html /about.html
REDIRECTS

HTTP_HEADERS=$(curl --silent --show-error \
  -D - -o /dev/null \
  -H 'Host: socket23.com' \
  "http://127.0.0.1:$HTTP_PORT/redirect-check")
grep -qE '^HTTP/[0-9.]+ 301' <<<"$HTTP_HEADERS"
grep -qi '^location: https://socket23.com/redirect-check' <<<"$HTTP_HEADERS"

[[ "$(docker inspect --format '{{.Config.User}}' "$CID")" == "101:101" ]]
if docker exec "$CID" sh -c 'touch /usr/share/nginx/html/should-not-write' >/dev/null 2>&1; then
  echo 'read-only filesystem assertion failed' >&2
  exit 1
fi

echo "Smoke test passed: image=$IMAGE personal-home=ok case-study=ok discovery=ok redirect=ok https=ok headers=ok form-none=ok legacy-redirects=ok static-cache=ok 404=ok nonroot=ok readonly=ok"
