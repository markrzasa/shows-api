THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
TF_DEPLOY_DIR := "$(THIS_DIR)/infra/deploy"
TF_ENV_VARS := "$(THIS_DIR)/infra/env/$(ENV)/terraform.tfvars"
TF_PLAN := "$(THIS_DIR)/infra/deploy/terraform.tfplan"
TEST_URL := "http://localhost:8000"

requirements:
	pip install -r $(THIS_DIR)/python/requirements.txt

test-requirements:
	pip install -r $(THIS_DIR)/python/tests/requirements.txt

check-env:
ifndef ENV
	$(error ENV is undefined)
endif

init:
	cd $(TF_DEPLOY_DIR); terraform init

plan: check-env init
	cd $(TF_DEPLOY_DIR); terraform plan -var environment=$(ENV) -var-file $(TF_ENV_VARS) -out $(TF_PLAN)

apply: check-env
	cd $(TF_DEPLOY_DIR); terraform apply $(TF_PLAN)

destroy-prompt: check-env
	cd $(TF_DEPLOY_DIR); terraform destroy -var environment=$(ENV) -var-file $(TF_ENV_VARS)

providers-lock:
	cd $(TF_DEPLOY_DIR); terraform providers lock -platform=windows_amd64 -platform=darwin_amd64 -platform=linux_amd64

postgres-up:
	docker-compose -f $(THIS_DIR)/compose/postgres/docker-compose.yml up -d

postgres-down:
	docker-compose -f $(THIS_DIR)/compose/postgres/docker-compose.yml down

postgres-down-rm-volume:
	docker-compose -f $(THIS_DIR)/compose/postgres/docker-compose.yml down -v

run-app: requirements
	uvicorn main:app --app-dir python/app --reload

lint:
	flake8 --config $(THIS_DIR)/flake8.ini $(THIS_DIR)/python/

api-tests: requirements test-requirements
	python -m unittest discover -s $(THIS_DIR)/python/tests/api/

unit-tests: requirements test-requirements
	pytest --cov=app --cov=lib --cov-report=html:reports/html_dir $(THIS_DIR)/python/tests/unit/

code-quality: lint unit-tests
