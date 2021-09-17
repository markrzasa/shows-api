THIS_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
TF_DIR := $(THIS_DIR)/terraform
TF_DEPLOY_DIR := $(TF_DIR)/deploy
TF_ENV_DIR := "$(TF_DIR)/env/$(ENV)"
TF_ENV_VARS := $(TF_ENV_DIR)/terraform.tfvars
TF_PLAN := $(TF_DEPLOY_DIR)/terraform.tfplan
TEST_URL := http://localhost:8000

requirements:
	pip install -r $(THIS_DIR)/python/requirements.txt

test-requirements:
	pip install -r $(THIS_DIR)/python/tests/requirements.txt

check-env:
ifndef ENV
	$(error ENV is undefined)
endif

init:
	cd $(TF_DEPLOY_DIR); terraform init -backend=true -backend-config=$(TF_ENV_DIR)/terraform.backend

plan: check-env init
	cd $(TF_DEPLOY_DIR); terraform plan -var environment=$(ENV) -var-file $(TF_ENV_VARS) -out $(TF_PLAN)

apply: check-env
	cd $(TF_DEPLOY_DIR); terraform apply $(TF_PLAN)

destroy-prompt: check-env
	cd $(TF_DEPLOY_DIR); terraform destroy -var environment=$(ENV) -var-file $(TF_ENV_VARS)

providers-lock:
	cd $(TF_DEPLOY_DIR); terraform providers lock -platform=windows_amd64 -platform=darwin_amd64 -platform=linux_amd64

tfsec:
	cd $(TF_DEPLOY_DIR); tfsec

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

code-quality: tfsec lint unit-tests
