REG ?= ghcr.io/socket1923
NAME ?= site-infrastructure
TAG ?= $(shell git rev-parse --short=12 HEAD)
IMG := $(REG)/$(NAME):$(TAG)
PLATFORMS ?= linux/amd64,linux/arm/v7

.PHONY: build multiarch push test config run up down swarm-deploy

build:
	docker build -t $(IMG) .

multiarch:
	docker buildx build --platform $(PLATFORMS) -t $(IMG) --provenance=mode=max --sbom=true .

push:
	docker buildx build --platform $(PLATFORMS) -t $(IMG) --provenance=mode=max --sbom=true --push .

test:
	../scripts/smoke-test.sh $(IMG)

config:
	TLS_FULLCHAIN_FILE=$${TLS_FULLCHAIN_FILE:-./.test-certs/fullchain.pem} \
	TLS_PRIVKEY_FILE=$${TLS_PRIVKEY_FILE:-./.test-certs/privkey.pem} \
	docker compose config >/dev/null
	IMAGE_REF=$(IMG) docker stack config -c stack.yaml >/dev/null

run:
	docker compose up --build -d

up: run
	docker compose ps

down:
	docker compose down -v --remove-orphans

swarm-deploy:
	@test -n "$(IMAGE_REF)" || (echo "IMAGE_REF must be an immutable ghcr.io digest" >&2; exit 1)
	IMAGE_REF=$(IMAGE_REF) docker stack deploy --prune -c stack.yaml web
