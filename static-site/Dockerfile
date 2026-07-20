FROM nginxinc/nginx-unprivileged:stable-alpine@sha256:dcea25a6593307a74b09e59a47f8695c4d56943750e45add532ae0bf8b24bfd6

LABEL org.opencontainers.image.source="https://github.com/socket1923/site-infrastructure" \
      org.opencontainers.image.description="Socket23 static website" \
      org.opencontainers.image.licenses="MIT"

COPY --chown=101:101 nginx.conf /etc/nginx/conf.d/default.conf
COPY --chown=101:101 site/ /usr/share/nginx/html/

USER 101:101
EXPOSE 8080 8443

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- --no-check-certificate https://127.0.0.1:8443/ >/dev/null || exit 1
