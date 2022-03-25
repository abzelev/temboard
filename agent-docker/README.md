# temBoard agent

temBoard is a web application for managing clusters for PostgreSQL instances.

This docker image targets development environment and demo.


## Environment variables

`temboard-agent.conf` is generated from environment variables.

- `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER` and `PGPASSWORD` for access to
  repository.
- `TEMBOARD_GROUPS`: groups of this agent.
- `TEMBOARD_HOSTNAME`: PostgreSQL instance FQDN
- `TEMBOARD_KEY`: agent secret key
- `TEMBOARD_LOGGING_LEVEL`: standard python logging level: `DEBUG`, `INFO`, etc.
- `TEMBOARD_UI_URL`, `TEMBOARD_UI_USER` and `TEMBOARD_UI_PASSWORD`: URL and
  credentials of the UI for autoregister and monitoring report.
- `TEMBOARD_SSL_CA`, `TEMBOARD_SSL_CERT` and `TEMBOARD_SSL_KEY` for HTTPS.
- `TEMBOARD_USERS`: a space separated list of `login:password`.
