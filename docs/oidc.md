# OIDC Support

- References
  - [5.1.1.1.1.](https://github.com/ietf-wg-scitt/draft-ietf-scitt-architecture/blob/main/draft-ietf-scitt-architecture.md#comment-on-oidc)

## Dependencies

Install the SCITT API Emulator with the `oidc` extra.

```console
$ pip install -e .[oidc]
```

## Usage example with GitHub Actions

Expose the server to the internet. localhost.run or ngrok are common options if
you need to exposed a NAT'd machine.

```console
$ ssh -nT -R 80:localhost:8080 nokey@localhost.run 2>&1 | grep --line-buffered 'tunneled with tls termination'
aaaaaaaaaaaaaa.lhr.life tunneled with tls termination, https://aaaaaaaaaaaaaa.lhr.life
```

Create the middleware config file.

**oidc-middleware-config.json**

```json
{
    "issuer": "https://token.actions.githubusercontent.com",
    "audience": "https://scitt.example.com"
}
```

Set config `audience` to the publicly accessible URL of the SCITT instance.

```console
$ echo "$(cat oidc-middleware-config.json)" \
    | jq '.audience = "https://aaaaaaaaaaaaaa.lhr.life"' \
    | tee oidc-middleware-config.json.new \
    && mv oidc-middleware-config.json.new oidc-middleware-config.json
```

Start the SCITT instance using the `OIDCAuthMiddleware` and associated config.

```console
$ scitt-emulator server --port 8080 --workspace workspace/ --tree-alg CCF \
    --middleware scitt_emulator.oidc:OIDCAuthMiddleware \
    --middleware-config-path oidc-middleware-config.json
```

Create two GitHub Actions Workflows.

References:

- https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/using-openid-connect-with-reusable-workflows
- https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect

The first is a reusable which will be what you extend.

**.github/workflows/notarize_reusable.yml**

```yaml
name: "SCITT Notary: Reusable Workflow"

on:
  workflow_call:
    inputs:
      scitt-url:
        description: 'URL of SCITT instance'
        type: string
      payload:
        description: 'Payload for claim'
        type: string

jobs:
  notarize:
    runs-on: ubuntu-latest
    env:
      SCITT_URL: '${{ inputs.scitt-url }}'
      PAYLOAD: '${{ inputs.payload }}'
    steps:
      - name: Get OIDC token to use as bearer token for auth to SCITT
        uses: actions/github-script@v6
        id: github-oidc
        with:
          script: |
            const {SCITT_URL} = process.env;
            const coredemo = require('@actions/core');
            coredemo.setOutput('token', await coredemo.getIDToken(SCITT_URL));
      - name: Create claim
        run: |
          scitt-emulator client create-claim --issuer did:web:example.org --content-type application/json --payload "${PAYLOAD}" --out claim.cose
      - name: Submit claim
        env:
          OIDC_TOKEN: '${{ steps.github-oidc.outputs.token }}'
        run: |
          scitt-emulator client submit-claim --token "${OIDC_TOKEN}" --url "${SCITT_URL}" --claim claim.cose --out claim.receipt.cbor
```

The second is a dispatchable flow which uses the reusable workflow.

**.github/workflows/notarize.yml**

```yaml
name: "SCITT Notary"

on:
  workflow_dispatch:
    inputs:
      scitt-url:
        description: 'URL of SCITT instance'
        type: string

jobs:
  notarize:
    permissions:
      id-token: write
    uses: '.github/workflows/notarize_reusable.yml'
    with:
      scitt-url: '${{ github.event.inputs.scitt-url }}'
      payload: '${{ toJSON(github.event) }}'
```

Dispatch the workflow

```console
$ gh workflow run notarize.yml -F scitt-url=https://aaaaaaaaaaaaaa.lhr.life
```
