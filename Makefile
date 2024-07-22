.PHONY: help startTest updateTest stopTest
.EXPORT_ALL_VARIABLES:

PROJECT_SLUG := "scrapper"
APP_NAME := $(PROJECT_SLUG)-backend
DOCKER_HUB := beafdocker

help: ## Help for project
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ANSI color codes
GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

## Docker
startTest: ## Start docker development environment
	@echo "$(YELLOW)Starting docker environment...$(RESET)"
	docker compose -p $(PROJECT_SLUG) up --build

# This target can be used in a separate terminal to update any containers after a change in config without restarting (environment variables, requirements.txt, etc)
updateTest:  ## Update test environment containers (eg: after config changes)
	docker compose -p $(PROJECT_SLUG) up --build -d

stopTest: ## Stop test development environment
	@COMPOSE_PROJECT_NAME=$(PROJECT_SLUG) docker compose down


# Utilities
lint: ## Format backend code
	@echo "$(YELLOW)Running linters for backend...$(RESET)"
	@cd backend && make format


# Backend Deployment
build: ## Build docker image for the project
	@echo "$(YELLOW)Building project image...$(RESET)"
	docker build -f backend/Dockerfile -t $(APP_NAME) ./backend

stage: ## Prepare postges database
	@echo "$(YELLOW)Staging for deployment...$(RESET)"
	docker tag $(APP_NAME):latest $(DOCKER_HUB)/$(APP_NAME):latest
	docker push $(DOCKER_HUB)/$(APP_NAME):latest

# Helpers
pre-commit:
	npx concurrently --kill-others-on-fail --prefix "[{name}]" --names "backend:lint,backend:test" \
	--prefix-colors "bgRed.bold.white,bgGreen.bold.white,bgBlue.bold.white,bgMagenta.bold.white" \
	"docker exec react-router-backend-1 make format" \
	"docker exec react-router-backend-1 make test"
