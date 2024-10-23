# Copyright (c) SCITT Authors
# Licensed under the MIT License.
from scitt_software_supply_chain_middleware.github_webhook_notary import GitHubWebhookNotary


async def test_app(app):
    client = app.test_client()
    response = await client.get('/')
    assert response.status_code == 200
