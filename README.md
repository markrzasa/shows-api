# shows-api

This repo contains code to stand up a service that manages a catalog of shows. The service is backed by Google's App 
Engine and Cloud SQL. Details of the API are available at the `/docs` endpoint.

## Infrastructure

Before deploying infrastructure, make sure to configure credentials to allow the Google Terraform provider to make
requests to GCP by following [these](https://registry.terraform.io/providers/hashicorp/google/latest/docs/guides/getting_started#adding-credentials)
instructions.

Infrastructure for this application is deployed as follows.

Run this command to create a Terraform plan.
```
make ENV=demo plan
```

Run this command to apply the plan.
```
make ENV=demo apply
```

When you're done, run this command to delete the infrastructure.
```
make ENV=demo destroy-prompt
```

## Testing

### Lint and Unittests

Run the following command to lint and unittest Python code:
```
make code-quality
```

### API Tests

API tests can be run against a deployed service as follows:
```
make TEST_URL=${APP_INSTANCE_URL} api-tests
```

### Running the Service Locally

The service can be run locally. First use docker-compose to run Postgres in a container:
```
make postgres-up
```

The shows API service can then be run as follows:
```
make run-app
```

The API tests can then be run like this:
```
make api-tests
```
