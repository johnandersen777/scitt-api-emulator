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

> The following is a demo of Bob receiving a GitHub push webhook via
> `GitHubWebhookNotaryMiddleware`. The SCITT instance hashes the corresponding
> tar.gz archive of the repo and submits in-toto style SLSA evidence as the
> statement payload to Bob's append only log. Alice's instance is receiving
> events from Bob's via federation. Her instance (TODO evaluate against policy,
> shouldi?) determines the statement worthy of inclusion in her append-only log
> and issues a statement and receipt for her TS. This follows the S2C2F ING-4
> pattern.

[![asciicast-of-hash-of-tar-gz](https://asciinema.org/a/622103.svg)](https://asciinema.org/a/622103)

```graphql
query ($owner: String!, $repo: String!, $commit_colon_file_path: String!) {
  repository(owner: $owner, name: $repo) {
    object(expression: $commit_colon_file_path) {
      ... on Blob {
        oid
      }
    }
  }
}
```

```console
$ gh api graphql --jq .data.repository.object.oid -F owner='scitt-community' -F repo='scitt-api-emulator' -F commit_colon_file_path="$(git log -n 1 --format=%H):setup.py" -F "query=@scitt_software_supply_chain_middleware/git_blob.graphql"
$ git rev-parse "$(git log -n 1 --format=%H):setup.py"
```

From in-toto example:

```json
{
    "_type": "https://in-toto.io/Statement/v1",
    "subject": [
        {
            "digest": {
                "gitCommit": "d20ace7968ba43c0219f62d71334c1095bab1602"
            }
        }
    ],
    "predicateType": "https://in-toto.io/attestation/test-result/v0.1",
    "predicate": {
        "result": "PASSED",
        "configuration": [{
            "name": ".github/workflows/scorecard.yml",
            "downloadLocation": "https://github.com/in-toto/in-toto/blob/d20ace7968ba43c0219f62d71334c1095bab1602/.github/workflows/scorecard.yml",
            "digest": {
                "gitBlob": "ebe4add40f63c3c98bc9b32ff1e736f04120b023"
            }
        }],
        "url": "https://github.com/in-toto/in-toto/actions/runs/4425592351",
        "passedTests": [
            "scorecard greater than 5.0"
        ],
        "warnedTests": [],
        "failedTests": []
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
