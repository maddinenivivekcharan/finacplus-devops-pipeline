import os
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, Response

START_TIME = time.time()


def create_app() -> Flask:
    app = Flask(__name__)
    service_name = os.getenv("SERVICE_NAME", "finacplus-devops-pipeline")
    build_sha = os.getenv("BUILD_SHA", "local")
    environment = os.getenv("APP_ENV", "dev")

    @app.get("/")
    def index():
        return jsonify(
            service=service_name,
            status="running",
            environment=environment,
            build_sha=build_sha,
        )

    @app.get("/healthz")
    def healthz():
        return jsonify(status="ok")

    @app.get("/readyz")
    def readyz():
        return jsonify(status="ready")

    @app.get("/version")
    def version():
        return jsonify(
            service=service_name,
            build_sha=build_sha,
            environment=environment,
            started_at=datetime.fromtimestamp(START_TIME, tz=timezone.utc).isoformat(),
        )

    @app.get("/metrics")
    def metrics():
        uptime = max(0, time.time() - START_TIME)
        body = "\n".join(
            [
                "# HELP finacplus_app_up Application health status.",
                "# TYPE finacplus_app_up gauge",
                "finacplus_app_up 1",
                "# HELP finacplus_app_uptime_seconds Application process uptime.",
                "# TYPE finacplus_app_uptime_seconds counter",
                f"finacplus_app_uptime_seconds {uptime:.3f}",
                "",
            ]
        )
        return Response(body, mimetype="text/plain; version=0.0.4")

    return app


app = create_app()
