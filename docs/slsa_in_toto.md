# SLSA (in-toto style)

## Webhook endpoint

Targets are new commits, branches, tags, and their CI/CD (status check) results

- Transforms GitHub webhook payloads into statements
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/v1/statement.md
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/predicates/test-result.md
  - https://github.com/in-toto/attestation/blob/99d851228fe284c66b2cde353a6693c5eff69db1/spec/predicates/cyclonedx.md
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
