# Contributing


[dalibo/temboard]: https://github.com/dalibo/temboard

## Reporting an Issue & Submitting a Patch

We use the [dalibo/temboard] project to track issue and review
contributions. Fork the main repository and open a PR against
`master` as usual.


## Development Environment Setup

You can quickly set up a dev env with virtualenv and Docker Compose. Running
development version of UI and agent requires two shells, one for the UI and one
for the agent.

Get temBoard UI and agent sources:

```console
$ git clone --recursive https://github.com/dalibo/temboard.git
$ cd temboard/
```

The `develop` make target creates a virtual environment for Python 3.6,
installs temBoard and its dependencies, development tools, starts services and
initialize temBoard repository.

``` console
$ make develop
...
2020-03-24 17:09:05,937 [30557] [migrator        ]  INFO: Database is up to date.
Initialized role temboard and database temboard.
docker-compose up -d
temboard_repository_1 is up-to-date
Creating temboard_instance_1 ... done
Creating temboard_agent_1    ... done

$ .venv-py3.6/bin/temboard --debug
 INFO: Starting temboard 8.0.dev0.
 INFO: Found config file /home/.../temboard/temboard.conf.
 INFO: Running on Debian GNU/Linux 11 (bullseye).
 INFO: Using Python 3.6.8 (/home/.../.cache/pyenv/versions/temboard-uoBqmXGk-py3.6/bin/python) and Tornado 4.4.3 .
 INFO: Using libpq 11.5, Psycopg2 2.8.6 (dt dec pq3 ext lo64) and SQLAlchemy 1.3.24 .
2022-03-16 14:08:06,425 temboardui[1593889]: [pluginsmgmt     ]  INFO: Loaded plugin 'dashboard'.
...
2022-03-16 14:08:06,489 temboardui[1593889]: [temboardui      ]  INFO: Serving temboardui on https://0.0.0.0:8888
...
```

Go to https://127.0.0.1:8888/ to access temBoard running with your code!

You now need to run an agent and register it in UI. Open a second shell for
managing the agent and execute the following commands.

``` console
$ docker-compose exec agent0 /bin/bash
root@91cd7e12ac3e:/var/lib/temboard-agent# sudo -u postgres hupper -m temboardagent.scripts.agent
 INFO: Starting temboard-agent 8.0.dev0.
 INFO: Found config file /etc/temboard-agent/temboard-agent.conf.
2020-08-11 14:29:45,834 [ 3769] [app             ] DEBUG: Looking for plugin activity.
...
```

Now register the agent in UI, using host `0.0.0.0`, port `2345` and key
`key_for_agent`. The monitored Postgres instance is named `postgres0.dev`.

Beware that two Postgres instances are set up with replication. The primary
instance may be either postgres0 or postgres1. See below for details.


### Execute UI unit tests

Use pytest to run unit tests:

``` console
$ cd ui/
ui/$ pytest tests/unit
...
==== 31 passed, 10 warnings in 1.10 seconds ======
ui/$
```


### Execute UI func tests

Go to tests/func and run docker-compose:

``` console
$ cd ui/tests/func
ui/tests/func/$ docker-compose up --force-recreate --always-recreate-deps --renew-anon-volumes --abort-on-container-exit ui
...
```

Functionnal tests are executed **outside** temboard process. UI is installed and
registered using regular tools : pip, dpkg or yum, auto_configure.sh, etc. A
real Postgres database is set up for the repository

Tests are written in Python with pytest.

For development purpose, a `docker-compose.yml` file describe the setup to
execute functionnal tests almost like on Circle CI. The main entry point is
`tests/func/run.sh` which is responsible to install temboard, configure it and
call pytest.

On failure, the main container, named `ui`, wait for you to enter it and debug.
Project tree is mounted at `/workspace`.

``` console
ui/tests/func/$ docker-compose exec ui /bin/bash
[root@ccb2ec0d78cb workspace]# tests/func/run.sh --pdb -x
…
```


## Testing with Postgres replication

Two postgres instance are up with replication. You can execute a second agent
for it likewise:

``` console
$ docker-compose exec agent1 /bin/bash
root@91cd7e12ac3e:/var/lib/temboard-agent# sudo -u postgres hupper -m temboardagent.scripts.agent
 INFO: Starting temboard-agent 8.0.dev0.
 INFO: Found config file /etc/temboard-agent/temboard-agent.conf.
2022-01-11 10:12:55,130 [ 1568] [app             ] DEBUG: Looking for plugin activity.
...
```

bash history is shared amongst these two containers.

In UI, register the second agent with address 0.0.0.0, port 2346 instead of
2345, with the same key `key_for_agent`. The instance FQDN is `postgres1.dev`.

The script `docker/dev-switchover.sh` triggers a switchover between the two
postgres instances. Executing `docker/dev-switchover.sh` one more time restore
the original topology.


## Editing Documentation

The documentation is written in markdown and built with `mkdocs`

``` console
$ mkdocs serve
INFO     -  Building documentation...
INFO     -  Cleaning site directory
INFO     -  The following pages exist in the docs directory, but are not included in the "nav" configuration:
              - alerting.md
              - postgres_upgrade.md
INFO     -  Documentation built in 0.42 seconds
INFO     -  [16:21:24] Serving on http://127.0.0.1:8000/
...
```

Go to http://127.0.0.1:8000/ to view the documentation. mkdocs serve has hot
reload while you edit the documentation.


### Throw your development environment

If you want to trash development env, use `docker-compose down -v` and restart
from `make develop`.


## Entering Monitored PostgreSQL Instance with psql

Use the following command:

``` console
$ docker-compose exec agent0 sudo -iu postgres psql
psql (13.5 (Debian 13.5-0+deb11u1), server 14.1)
WARNING: psql major version 13, server major version 14.
         Some psql features might not work.
Type "help" for help.

postgres=#
```


### Monitoring another version of PostgreSQL

You can change the version of the monitored PostgreSQL instance by overriding
docker image in `docker-compose.override.yml`.

``` yml
# file docker-compose.override.yml
version: "2.4"

services:
  postgres:
    image: postgres:9.5-alpine
```

Now apply changes with `make develop`. Docker-compose will recreate `postgres`
and `agent` containers, thus you need to install and start the agent as
documented above.


### CSS

temBoard UI mainly relies on `Bootstrap`. The CSS files are compiled with
`SASS`. Execute all the following commands in ui/ directory.

In case you want to contribute on the styles, first install the nodeJS dev
dependencies:

```
npm install
```

Then you can either build a dist version of the css:
```
grunt sass:dist
```

Or build a dev version which will get updated each time you make a change in
any of the .scss files:
```
grunt watch
```


### Launching Multiple Agents

Default development environment instanciate a single PostgreSQL instance and
it's temBoard agent. Root Makefile offers two targets to help testing bigger
infrastructure :

- `make mass-agents` loops from 2345 to 2400 and instanciate a PostgreSQL
  instance and an agent to monitor it. Each instanciation requires you to type
  `y`. This allows to throttle instanciations and to stop when enough instances
  are up.
- `make clean-agents` trashes every existings instances from 2345 to 2400,
  without interaction. **Agent are not unregistered!**


## Coding style

An `.editorconfig` file is included at the root of the repository configuring
whitespace and charset handling in various programming language.
The [EditorConfig]( http://editorconfig.org/#download) site links to plugins for
various editors. See `.editorconfig` for a description of the conventions.
Please stick to this conventions.

Python syntax must conform to flake8. Our CI checks new code with flake8.


## Creating a New UI Database Schema Version

temBoard repository is versionned. A version is the name of a file in
`temboardui/model/versions`. Each file contains the code to execute to upgrade
to this version.

To create a new version, put a new file in `temboardui/model/versions/`
prefixed with a discrete number following the last version. As of now, version
file must ends with `.sql` and contains valid PostgreSQL SQL.

That's all. Use temboard-migratedb to check and upgrade temBoard repository.


## Contribution Workflow

Fork the project, commit in a branch and open a new GithUb PR on
https://github.com/dalibo/temboard.


## Building UI snapshot

You can build a snapshot RPM like this:

``` console
ui/$ make snapshot
ui/$ make -C packaging/rpm build-rhel8
```


## Releasing the Server

Releasing a new version of temBoard requires write access to master on [main
repository](https://github.com/dalibo/temboard), [PyPI
project](https://pypi.org/project/temboard), [Docker Hub
repository](https://hub.docker.com/r/dalibo/temboard) and Dalibo Labs YUM and
APT repositories.

For the tooling, you need Git 1.8+, a recent setuptools with wheel. For
distribution packaging, see ad-hoc documentation in `ui/packaging/`.

To release a new version:

- Move to ui/ directory.
- Checkout release branch (like v2).
- Choose the next version according to [PEP 440]
  (https://www.python.org/dev/peps/pep-0440/#version-scheme).
- Update `temboardui/version.py`, without committing.
- Generate and push commit and tag with `make release`.
- Push Python egg to PyPI using `make upload`.
- Build and upload RPM package with `make -C packaging/rpm all push`.
- Build and upload Debian package with `make -C packaging/deb all push`.


## Releasing the Agent

Releasing a new version of temBoard agent requires write access to
master on [main repository](https://github.com/dalibo/temboard-agent),
[PyPI project](https://pypi.org/project/temboard-agent) and [Docker Hub
repository](https://hub.docker.com/r/dalibo/temboard-agent).

For the tooling, you need Git 1.8+, a recent setuptools with wheel, and
twine. For debian packaging, see below.

Please follow these steps:

- Move to agent/ directory.
- Checkout the release branch, e.g. v2.
- Choose the next version according to [PEP 440](https://www.python.org/dev/peps/pep-0440/#version-scheme) .
- Update `temboardagent/version.py`, without committing.
- Generate commit and tag with `make release`.
- Push Python egg to PyPI using `make upload`.
- Build and push RPM packages using `make -C packaging/rpm all push`.
- Build and push debian packages using
  `make -C packaging/deb all push`.
- Trigger docker master build from
  <https://hub.docker.com/r/dalibo/temboard-agent/~/settings/automated-builds/>.


## Other documentation for maintainers

Checkout the RPM packaging README for the agent:

https://github.com/dalibo/temboard-agent/blob/master/packaging/rpm/README.rst
