# DevOps Insights - common tasks. Run `make help` for the list.

VENV          := backend/.venv
PYTHON        := $(VENV)/bin/python
CHART         := deploy/helm/devops-insights
KIND_CLUSTER  ?= devops-insights
IMAGE_TAG     := 0.2.0
NAMESPACE     := devops-insights
RELEASE       := devops-insights

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"} /^##@/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 5)} /^[a-zA-Z0-9_-]+:.*##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

##@ Local development (backend and frontend without Docker)

.PHONY: setup
setup: ## Create the Python virtualenv and install the backend with dev tools
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -e "backend[dev]"

.PHONY: db-up
db-up: ## Start only PostgreSQL and Ollama in Docker
	docker compose up -d postgres ollama ollama-init

.PHONY: migrate
migrate: ## Apply database migrations
	cd backend && ../$(PYTHON) -m devops_insights.migrate

.PHONY: run-backend
run-backend: ## Run the API with auto-reload on http://localhost:8000
	cd backend && ../$(VENV)/bin/uvicorn devops_insights.api.app:create_app --factory --reload --port 8000

.PHONY: run-frontend
run-frontend: ## Serve the frontend on http://localhost:8080 (proxies /api to the backend)
	python3 frontend/dev_server.py

.PHONY: run-collector
run-collector: ## Run the collector worker (collects now, then every 6 hours)
	cd backend && ../$(PYTHON) -m devops_insights.worker

.PHONY: collect
collect: ## Collect all repositories once and exit
	cd backend && ../$(PYTHON) -m devops_insights.worker --once

##@ Quality

.PHONY: test
test: test-backend test-frontend ## Run all tests

.PHONY: test-backend
test-backend: ## Run the backend tests (needs PostgreSQL: make db-up)
	cd backend && ../$(VENV)/bin/pytest

.PHONY: test-frontend
test-frontend: ## Run the frontend unit tests (uses Docker, no local Node needed)
	docker run --rm -v "$(CURDIR)/frontend":/app -w /app node:22-alpine npm test

.PHONY: lint
lint: ## Lint and check formatting (Python)
	cd backend && ../$(VENV)/bin/ruff check . && ../$(VENV)/bin/ruff format --check .

.PHONY: format
format: ## Format and auto-fix (Python)
	cd backend && ../$(VENV)/bin/ruff check --fix . && ../$(VENV)/bin/ruff format .

.PHONY: check
check: lint test helm-lint sync-check version-check ## Everything CI runs

##@ Docker Compose

.PHONY: up
up: ## Build and start the whole stack
	docker compose up -d --build
	@$(MAKE) --no-print-directory urls-compose

.PHONY: down
down: ## Stop the stack (data is kept)
	docker compose down

.PHONY: reset
reset: ## Stop the stack and DELETE its data (database, metrics, Grafana, AI model)
	docker compose down -v

.PHONY: ps
ps: ## Show container status
	docker compose ps

.PHONY: logs
logs: ## Follow the logs of all containers
	docker compose logs -f

##@ Kubernetes (kind)

.PHONY: images
images: ## Build the backend and frontend images
	docker build -t devops-insights-backend:$(IMAGE_TAG) backend
	docker build -t devops-insights-frontend:$(IMAGE_TAG) frontend

.PHONY: kind-up
kind-up: ## Create the local kind cluster with every component's port mapped (KIND_CLUSTER=name)
	kind create cluster --name $(KIND_CLUSTER) --config deploy/kubernetes/kind/cluster.yaml

.PHONY: kind-down
kind-down: ## Delete the local kind cluster
	kind delete cluster --name $(KIND_CLUSTER)

.PHONY: kind-load
kind-load: images ## Build the images and load them into the kind cluster
	kind load docker-image devops-insights-backend:$(IMAGE_TAG) devops-insights-frontend:$(IMAGE_TAG) --name $(KIND_CLUSTER)

.PHONY: k8s-deploy
k8s-deploy: ## Install or upgrade the Helm release on the current kubectl context
	helm upgrade --install $(RELEASE) $(CHART) -f $(CHART)/values-kind.yaml \
		--namespace $(NAMESPACE) --create-namespace --wait --timeout 10m

.PHONY: k8s-status
k8s-status: ## Show the pods of the release
	kubectl -n $(NAMESPACE) get pods

.PHONY: k8s-forward
k8s-forward: ## Publish the release on localhost with port-forward (clusters without port mappings)
	scripts/k8s-port-forward.sh $(NAMESPACE) $(RELEASE)

.PHONY: k8s-undeploy
k8s-undeploy: ## Uninstall the Helm release
	helm uninstall $(RELEASE) --namespace $(NAMESPACE)

.PHONY: argocd-install
argocd-install: ## Install Argo CD with login admin/admin (CONTEXT defaults to the kind cluster)
	scripts/argocd-install.sh $(or $(CONTEXT),kind-$(KIND_CLUSTER))

##@ OpenShift and verification

.PHONY: openshift-deploy
openshift-deploy: ## Build the images in OpenShift, install the chart and run the smoke test (after oc login)
	scripts/openshift-deploy.sh

.PHONY: smoke-test
smoke-test: ## Check a running Docker Compose stack end to end (21 checks)
	FRONTEND_URL=http://localhost:8080 GRAFANA_URL=http://localhost:3000 PROMETHEUS_URL=http://localhost:9090 scripts/smoke-test.sh

.PHONY: smoke-test-kind
smoke-test-kind: ## Check the kind deployment end to end
	FRONTEND_URL=http://localhost:30080 GRAFANA_URL=http://localhost:30300 PROMETHEUS_URL=http://localhost:30900 scripts/smoke-test.sh

##@ Helm and monitoring

.PHONY: helm-lint
helm-lint: ## Lint the chart and render it for kind and OpenShift
	helm lint $(CHART)
	helm lint $(CHART) -f $(CHART)/values-kind.yaml
	helm lint $(CHART) -f $(CHART)/values-openshift.yaml
	helm template $(RELEASE) $(CHART) -f $(CHART)/values-kind.yaml > /dev/null
	helm template $(RELEASE) $(CHART) -f $(CHART)/values-openshift.yaml > /dev/null

.PHONY: sync-monitoring
sync-monitoring: ## Copy the Grafana dashboard from monitoring/ into the Helm chart
	scripts/sync-monitoring.sh

.PHONY: version-check
version-check: ## Fail if the version fields disagree
	scripts/version.sh check

.PHONY: sync-check
sync-check: ## Fail if the chart's copy of the monitoring files is out of date
	scripts/sync-monitoring.sh --check

##@ Addresses

.PHONY: urls-compose urls-kind urls-openshift
urls-compose: ## Print every URL and login (Docker Compose)
	@scripts/urls.sh compose
urls-kind: ## Print every URL and login (kind)
	@scripts/urls.sh kind
urls-openshift: ## Print every URL and login (OpenShift, needs oc)
	@scripts/urls.sh openshift
