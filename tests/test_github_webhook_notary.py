# Copyright (c) SCITT Authors
# Licensed under the MIT License.
import types
import contextlib

import pytest
from quart import Quart, request

from scitt_emulator.signals import SCITTSignals
from scitt_software_supply_chain_middleware.github_webhook_notary import (
    GitHubWebhookNotaryMiddleware,
)


@pytest.fixture
async def test_app():
    app = Quart(__name__)

    # See http://flask.pocoo.org/docs/latest/config/
    app.config.update(dict(DEBUG=True))
    app.config.update({})

    # See https://blinker.readthedocs.io/en/stable/#blinker.base.Signal.send
    app.signals = SCITTSignals(
        add_background_task=app.add_background_task,
    )

    app.asgi_app = GitHubWebhookNotaryMiddleware(app, None)

    async with app.test_app() as test_app:
        yield test_app


@pytest.fixture
async def test_client(test_app):
    return test_app.test_client()


class MockAiohttpResponseContent:
    def __init__(self, content):
        self._content = content

    async def read(self, _length):
        return self._content

    @classmethod
    @contextlib.asynccontextmanager
    async def response(cls, status, content_bytes):
        yield types.SimpleNamespace(
            status=status,
            content=cls(content_bytes),
        )


@pytest.mark.parametrize("anyio_backend", ["asyncio"])
async def test_github_webhook_notary_event_push_statement_archive_tar_gz(
    anyio_backend,
    test_client,
    mocker,
):
    # TODO Capture event with asyncio.Queue or something
    # test_app.signals.federation.submit_claim.connect

    mocker.patch(
        "aiohttp.ClientSession.get",
        return_value=MockAiohttpResponseContent.response(200, b""),
    )

    response = await test_client.post(
        "/github-webhook-notary/org_name/repo_name",
        json={
            "repository": {"full_name": "org/repo"},
            "hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        },
        headers={"X-GitHub-Event": "push"},
    )
    assert response.status_code == 200

    # TODO Ensure signal data was correct
