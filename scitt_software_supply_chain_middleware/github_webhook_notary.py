# Copyright (c) SCITT Authors.
# Licensed under the MIT License.
"""
- TODO

    - https://slsa.dev/spec/v1.0/provenance
"""
import os
import sys
import json
import base64
import aiohttp
import hashlib
import pathlib
import tempfile
import subprocess
import dataclasses
import concurrent.futures

from scitt_emulator.create_statement import create_claim as create_statement
from bovine_herd.server.utils import path_from_request
from quart import Quart, Blueprint, current_app, request, jsonify, send_from_directory


logger = logging.getLogger(__name__)

github_webhook_notary = Blueprint(
    "github_webhook_notary", __name__, url_prefix="/github-webhook-notary"
)


@dataclasses.dataclass
class GitHubWebhookNotaryConfig:
    signals: SCITTSignals
    session: aiohttp.ClientSession
    executor: concurrent.futures


async def get_sha(executor, session, url):
    sha384_instance = hashlib.sha384()
    async with session.get(url) as resp:
        while chunk := await resp.content.read(2**16):
            loop = asyncio.get_event_loop()
            chunk = await loop.run_in_executor(executor, sha384_instance.update, chunk)
            checksum = sha384_instance.hexdigest()
    return checksum


def get_tar_url(payload):
    return f'https://github.com/{payload["repository"]["full_name"]}/archive/{payload["hash"]}.zip'


def attestation_fields(name, rd):
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{"name": name, "digest": {"sha384": sha_chksm}}],
        "predicateType": "https://in-toto.io/Statement/v1",
    }


@github_webhook_notary.route("/<org_name>/<repo_name>", methods=["POST"])
async def github_webhook_notary_post_route(
    org_name: str, repo_name: str
) -> tuple[str, int]:
    # TODO Webhook secret hash validation
    event = request.headers.get("X-GitHub-Event")
    if event != "push":
        return (
            jsonify(
                {
                    "status": "failure",
                    "error": {"detail": "This route only accepts push events"},
                }
            ),
            400,
        )

    config = current_app.config[github_webhook_notary.name]

    payload = json.loads(await request.get_data())
    commit_archive_url = get_tar_url(payload)
    sha_chksm = await get_sha(config.executor, config.session, commit_archive_url)
    rd = generate_resource_descriptor(sha_chksm, commit_archive_url)
    attestation = attestation_fields(commit_archive_url, rd)

    with tempfile.TemporaryDirectory() as tempdir:
        statement_path = pathlib.Path(tempdir, "statement.cose")

        create_statement(
            # TODO issuer=None means ephemeral key, can we sign with something
            # persistent to this instance that's exportable? Maybe add OIDC
            # routes to this blueprint and a key to the config for this
            # blueprint?
            None,
            f"repo:{org_name}/{repo_name}:type:slsa:artifact:tar.gz",
            "application/json",
            attestation,
            private_key_pem_path=None,
        )

        await signals.federation.submit_claim.send_async(
            current_app,
            claim=statement_path.read_bytes(),
        )

    return (
        jsonify({"status": "success"}),
        400,
    )


def GitHubWebhookNotary(
    app: Quart,
    *,
    blueprint: Optional[Blueprint] = github_webhook_notary,
) -> Quart:
    @app.before_serving
    async def startup():
        if blueprint.name not in app.config:
            config = GitHubWebhookNotaryConfig(
                signals=app.signals,
                session=await aiohttp.ClientSession(trust_env=True).__aenter__(),
                executor=concurrent.futures.ThreadPoolExecutor(
                    max_workers=len(os.sched_getaffinity(0)) * 4,
                ).__enter__(),
            )
            app.config[blueprint.name] = config

    @app.after_serving
    async def shutdown():
        config = app.config[blueprint.name]
        config.executor.__exit__(None, None, None)
        await config.session.__aexit__(None, None, None)
        del app.config[blueprint.name]

    app.register_blueprint(blueprint)

    return app


class GitHubWebhookNotaryMiddleware:
    def __init__(self, app, config_path: pathlib.Path):
        self.app = app
        self.asgi_app = app.asgi_app
        self.config = {}
        if config_path and config_path.exists():
            self.config = json.loads(config_path.read_text())

        GitHubWebbookNotary(self.app)

    async def __call__(self, scope, receive, send):
        return await self.asgi_app(scope, receive, send)


import os
import json
import asyncio
import logging
import pathlib
import argparse
import concurrent.futures

import yaml


async def coro_for_loop_run_in_executor(loop, pool, non_async_func, *args):
    return await loop.run_in_executor(pool, non_async_func, *args)


async def search_sbom_for_deps_in_question(loop, tg, pool, root_dir, in_question, path):
    sbom_as_dict = await tg.create_task(
        coro_for_loop_run_in_executor(
            loop,
            pool,
            lambda path: yaml.safe_load(pathlib.Path(path).read_text()),
            path,
        )
    )
    if not isinstance(sbom_as_dict, dict):
        return
    packages = sbom_as_dict.get("packages", [])
    if not isinstance(packages, list):
        return
    for package in packages.items():
        version_info = package.get("versionInfo", None)
        if version_info is None:
            return
        package_name = package.get("name", None)
        if package_name is None:
            continue
        output = {
            "path": str(path.relative_to(root_dir)),
            "package_name": package_name,
            "version_info": version_info,
        }
        logger.debug("Checking: %s", json.dumps(output))
        if package_name in in_question:
            print(json.dumps(output))


async def search_sboms_for_deps_in_question(
    directory: str,
    in_question: str,
):
    loop = asyncio.get_event_loop()

    in_question = json.loads(pathlib.Path(in_question).read_text())

    # Gather all YAML versions of SBOMs files
    sbom_paths = list(pathlib.Path(directory).rglob("*.y[am]*l"))
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=len(os.sched_getaffinity(0)) * 4
    ) as pool:
        async with asyncio.TaskGroup() as tg:
            for i, path in enumerate(sbom_paths):
                if not path.is_file():
                    continue
                while len(tg._tasks) >= pool._max_workers:
                    await asyncio.sleep(0.05)
                tg.create_task(
                    search_sbom_for_deps_in_question(
                        loop, tg, pool, directory, in_question, path
                    )
                )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--directory", required=True, help="Root directory for searching SBOMs"
    )
    parser.add_argument(
        "--in_question", required=True, help="File containing deps in question"
    )
    parser.add_argument("--log", required=False, help="Log level")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log.upper(), logging.DEBUG))

    asyncio.run(search_sboms_for_deps_in_question(**vars(args)))


if __name__ == "__main__":
    main()
