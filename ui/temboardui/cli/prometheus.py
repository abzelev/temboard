# Setup and run Prometheus for temBoard.
#
# This is a standalone Prometheus instance, for testing purpose only.
# It is not intended to be used in production.
#
# Until 9.0 the command is not exposed.
# Run with python -m temboardui.cli.prometheus.
#
# Requires a running temboard instance aside to expose metrics.
#
# Dev Grafana (http://localhost:3000) is setup to use this Prometheus as
# `temBoard prometheus` with a dedicated dashboard.
#
import logging
import os
import signal
import sys
import subprocess
from datetime import datetime

import jinja2

import temboardui
from ..model import Session, orm
from ..toolkit.app import SubCommand
from ..toolkit.errors import UserError
from ..toolkit.services import Service
from .app import app


logger = logging.getLogger(__package__ + ".prometheus")


@app.command
class Prometheus(SubCommand):
    """Standalone Prometheus for temBoard.

    For testing purpose only.

    """

    def main(self, args):
        if not self.app.config.monitoring.prometheus:
            raise UserError("missing prometheus binary")

        prometheus = PrometheusService(
            app=self.app,
            setproctitle=self.app.webservice.setproctitle,
        )
        with prometheus:
            prometheus.run()


class PrometheusService(Service):
    def __init__(self, **kwargs):
        super(PrometheusService, self).__init__(
            name="prometheus manager",
            **kwargs,
        )
        self.proc = None

    @property
    def pidfile(self):
        return self.app.config.temboard.home + "/prometheus.pid"

    @property
    def home(self):
        return self.app.config.temboard.home + "/prometheus"

    def serve(self):
        self.terminate_running_prometheus(self.pidfile)

        logger.info("Provisionning Prometheus in %s.", self.home)
        provision_prometheus(self.app, self.home)
        logger.info("Starting %s.", self.app.config.monitoring.prometheus)
        cmd = [
            self.app.config.monitoring.prometheus,
            f"--config.file={self.home}/prometheus.yml",
            # 0.0.0.0 is reachable from dev grafana for testing purpose.
            # Once we have alertmanager, use localhost.
            "--web.listen-address=0.0.0.0:8890",
            "--log.level=debug",
            "--storage.tsdb.retention.time=1h",
        ]
        self.proc = subprocess.Popen(cmd, cwd=self.home)
        logger.info("Started Prometheus as PID %s.", self.proc.pid)
        with open(self.pidfile, "w") as fo:
            fo.write(str(self.proc.pid))
        self.setup_instances()
        logger.debug("Waiting prometheus service forever.")
        self.proc.wait()

    def terminate_running_prometheus(self, pidfile):
        if not os.path.exists(pidfile):
            return

        with open(pidfile) as fo:
            pid = fo.read()

        try:
            logger.debug("Eventually terminating Prometheus PID %s.", pid)
            os.kill(int(pid), signal.SIGTERM)
            logger.info("Prometheus running as PID %s. Terminating.", pid)
        except OSError:
            logger.debug("Spurious PID file %s.", pidfile)

    def setup_instances(self):
        session = Session()
        for (instance,) in session.execute(orm.Instances.all()):
            if not instance.discover:
                logger.debug("Skipping unreachable instance %s.", instance)
                continue
            if instance.discover["temboard"]["agent_version"] < "8":
                logger.debug("Skipping old agent %s.", instance)
                continue
            provision_instance(self.app, instance)
            self.proc.send_signal(signal.SIGHUP)

    def reload(self):
        super(PrometheusService, self).reload()
        if self.proc:
            self.proc.send_signal(signal.SIGHUP)

    def teardown(self):
        if not self.proc:
            return
        logger.info("Stopping Prometheus.")
        self.proc.terminate()
        self.proc = None
        os.unlink(self.app.config.temboard.home + "/prometheus.pid")


def provision_prometheus(app, home):
    logger.debug("Ensure prometheus home is created.")
    os.makedirs(home + "/instances.d", exist_ok=True)
    t = jinja2.Template(
        source=PROMETHEUS_CONFIG_TEMPLATE,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
    )
    conf = t.render(
        app=app,
        apikey="UNSECURE_DEV_APIKEY",
        home=home,
        now=datetime.utcnow(),
        temboard_version=temboardui.__version__,
    )
    with open(home + "/prometheus.yml", "w") as fo:
        os.chmod(fo.name, 0o600)
        fo.write(conf)


PROMETHEUS_CONFIG_TEMPLATE = """\
# This file is generated by temBoard. Do not edit.
#
# Generation Date: {{ now }}
# temBoard Version: {{ temboard_version }}
#
scrape_configs:
- job_name: temboard
  scrape_interval: 60s
  scheme: http
  authorization:
    type: Bearer
    credentials: {{ apikey }}
  file_sd_configs:
  - files:
    - instances.d/instance-*.yml
"""


def provision_instance(app, instance):
    logger.info("Provisionning %s.", instance)
    t = jinja2.Template(
        source=INSTANCE_CONFIG_TEMPLATE,
        trim_blocks=True,
        lstrip_blocks=True,
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
    )
    conf = t.render(
        app=app,
        instance=instance,
        now=datetime.utcnow(),
        temboard_version=temboardui.__version__,
    )
    path = "{}/prometheus/instances.d/instance-{}-{}.scrape.yml".format(
        app.config.temboard.home,
        instance.agent_address,
        instance.agent_port,
    )
    with open(path, "w") as fo:
        os.chmod(fo.name, 0o600)
        fo.write(conf)


INSTANCE_CONFIG_TEMPLATE = """\
# This file is generated by temBoard. Do not edit.
#
# Generation Date: {{ now }}
# temBoard Version: {{ temboard_version }}
#
- targets: [localhost:8888]
  labels:
    __metrics_path__: "/proxy/{{ instance.agent_address }}/{{ instance.agent_port }}/monitoring/metrics"
    instance:  "{{ instance.hostname }}:{{ instance.pg_port }}"
    agent:  "{{ instance.agent_address }}:{{ instance.agent_port }}"
"""  # noqa


if "__main__" == __name__:
    from ..__main__ import main

    sys.exit(main(argv=["prometheus"] + sys.argv[1:]))
