# SLSA (in-toto style)

## Webhook endpoint

Targets are new commits, branches, tags, and their CI/CD (status check) results

- Example GitHub Webhooks: https://gist.github.com/2bb4bb6d7a6abaa07cebc7c04d1cafa5
  - Push event
  - Workflow run and status check events
- Transforms GitHub webhook payloads into statements
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/v1/statement.md
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/predicates/test-result.md
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/predicates/cyclonedx.md
  - https://github.com/in-toto/attestation/blob/main/spec/v1/resource_descriptor.md
  - https://github.com/aquasecurity/trivy/blob/950e431f0f9759f053dc2fbe10e1869696c957f3/docs/docs/supply-chain/vex.md#openvex
- https://docs.github.com/en/rest/repos/contents?apiVersion=2022-11-28#download-a-repository-archive-tar

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "<NAME>",
      "digest": {"<ALGORITHM>": "<HEX_VALUE>"}
    },
    ...
  ],
  "predicateType": "https://in-toto.io/attestation/test-result/v0.1",
  "predicate": {
      "result": "PASSED|WARNED|FAILED",
      "configuration": ["<ResourceDescriptor>", ...],
      "url": "<URL>",
      "passedTests": ["<TEST_NAME>", ...],
      "warnedTests": ["<TEST_NAME>", ...],
      "failedTests": ["<TEST_NAME>", ...]
  }
}
```

- https://github.com/pdxjohnny/scitt-api-emulator/blob/demo-instance/docs/sbom_and_vex.md

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "<NAME>",
      "digest": {"<ALGORITHM>": "<HEX_VALUE>"}
    },
    ...
  ],
  "predicateType": "https://spdx.dev/Document/v2.3",
  "predicate": {
    "SPDXID" : "SPDXRef-DOCUMENT",
    "spdxVersion" : "SPDX-2.3",
    ...
  }
}
```

```python
from quart import Blueprint, request, jsonify
from quart.app import Quart
from hashlib import sha384
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import json, base64

repoapp = Blueprint("Repo", __name__, url_prefix="/")

executor = ThreadPoolExecutor(max_workers=5)

@repoapp.route("/github-webhook", methods=['POST'])
async def github_webhook():
    event = request.headers.get('X-GitHub-Event')  # choose a way to verify the request
    if event != "push":
        return jsonify({"status": "failure", "results": "This route only accepts push events."}), 400
    payload = json.loads(await request.get_data())
    commit_archive_url = get_tar_url(payload)
    sha_chksm = await get_sha(executor, commit_archive_url)
    rd = generate_resource_descriptor(sha_chksm, commit_archive_url)
    result = attestation_fields(commit_archive_url, rd)
    return jsonify(result), 200

async def get_sha(executor, url):
    sha384_instance = sha384()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            chunk = await resp.content.read(8192)
            loop = asyncio.get_event_loop()
            chunk = await loop.run_in_executor(repoapp.config["executor"], sha384_instance.update, chunk)
            checksum = sha384_instance.hexdigest()
    return checksum

def get_tar_url(payload):
    return f'https://api.github.com/repos/{payload["repository"]["full_name"]}/tarball/{payload["hash"]}'

def attestation_fields(name, rd):
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [{
            "name": name,
            "digest": { "sha384": sha_chksm }
        }],
        "predicateType": "https://in-toto.io/Statement/v1" # tihs is required but predicate is optional, do we need predicate?
    }
```
