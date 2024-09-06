.PHONY: help
.EXPORT_ALL_VARIABLES:

help:
	@echo "Usage: make <target>"
	@echo "Targets:"
	@echo "  startDev - Start Vercel development server"
	@echo "  deploy - Deploy to Vercel"
	@echo "  lint - Run linters for backend"
	@echo "  pre-commit - Run pre-commit hooks"

# ANSI color codes
GREEN=$(shell tput -Txterm setaf 2)
YELLOW=$(shell tput -Txterm setaf 3)
RED=$(shell tput -Txterm setaf 1)
BLUE=$(shell tput -Txterm setaf 6)
RESET=$(shell tput -Txterm sgr0)

## Vercel
dev: ## Start Vercel development server
	@echo "$(YELLOW)Starting Vercel development server...$(RESET)"
	vercel dev

deploy: ## Deploy to Vercel
	@echo "$(YELLOW)Deploying to Vercel...$(RESET)"
	vercel --prod

## Formatting
format: ## Format code for both Chrome extension and Python files
	@echo "$(BLUE)Formatting Chrome extension code...$(RESET)"
	npx prettier --write "chrome_extension/**/*.{js,json,html,css}"
	@echo "$(GREEN)Chrome extension code formatted.$(RESET)"
	@echo "$(BLUE)Formatting Python files...$(RESET)"
	black .
	@echo "$(GREEN)Python files formatted.$(RESET)"


# Helpers
pre-commit:
	npx concurrently --kill-others-on-fail --prefix "[{name}]" --names "api:lint" \
	--prefix-colors "bgRed.bold.white,bgGreen.bold.white,bgBlue.bold.white,bgMagenta.bold.white" \
	"make format"
