# Copyright (c) SCITT Authors.
# Licensed under the MIT License.
import sys
import json
import pathlib
import tempfile
import subprocess

from quart import send_from_directory


class SphinxDocsMiddleware:
    def __init__(self, app, config_path: pathlib.Path):
        self.app = app
        self.asgi_app = app.asgi_app
        self.config = {}
        if config_path and config_path.exists():
            self.config = json.loads(config_path.read_text())

        self.add_routes(app)

        @app.while_serving
        async def create_tempdir_for_docs():
            with tempfile.TemporaryDirectory() as tempdir:
                self.build_docs(tempdir)
                yield

    def build_docs(self, tempdir):
        self.built_singlehtml_dir_path = pathlib.Path(tempdir, "built_singlehtml_dir")
        subprocess.call(
            [
                sys.executable,
                "-m",
                "sphinx",
                "-b",
                "singlehtml",
                self.config["docs"],
                self.built_singlehtml_dir_path,
            ]
        )

    def add_routes(self, app):
        # TODO Blueprint?
        @app.get("/index.html")
        @app.get("/")
        async def index():
            return await send_from_directory(
                self.built_singlehtml_dir_path, "index.html"
            )

        @app.get("/_static/<path:path>")
        async def static_file(path):
            return await send_from_directory(
                self.built_singlehtml_dir_path.joinpath("_static"), path
            )

    async def __call__(self, scope, receive, send):
        return await self.asgi_app(scope, receive, send)
