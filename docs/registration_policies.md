# Registration Policies

- References
  - [5.2.2. Registration Policies](https://www.ietf.org/archive/id/draft-birkholz-scitt-architecture-02.html#name-registration-policies)

## Simple decoupled file based policy engine

The SCITT API emulator can deny entry based on presence of
`operation.policy.{insert,denied,failed}` files. Currently only for use with
`use_lro=True`.

This is a simple way to enable evaluation of claims prior to submission by
arbitrary policy engines which watch the workspace (fanotify, inotify, etc.).

[![asciicast-of-simple-decoupled-file-based-policy-engine](https://asciinema.org/a/620587.svg)](https://asciinema.org/a/620587)

Start the server

```console
$ rm -rf workspace/
$ mkdir -p workspace/storage/operations
$ timeout 0.5s scitt-emulator server --workspace workspace/ --tree-alg CCF --use-lro
Service parameters: workspace/service_parameters.json
^C
```

Modification of config to non-`*` insert policy. Restart SCITT API emulator server after this.

```console
$ echo "$(cat workspace/service_parameters.json)" \
    | jq '.insertPolicy = "allowlist.schema.json"' \
    | tee workspace/service_parameters.json.new \
    && mv workspace/service_parameters.json.new workspace/service_parameters.json
{
  "serviceId": "emulator",
  "treeAlgorithm": "CCF",
  "signatureAlgorithm": "ES256",
  "serviceCertificate": "-----BEGIN CERTIFICATE-----",
  "insertPolicy": "allowlist.schema.json"
}
```

Basic policy engine in two files

**enforce_policy.py**

```python
import os
import sys
import pathlib

policy_reason = ""
if "POLICY_REASON_PATH" in os.environ:
    policy_reason = pathlib.Path(os.environ["POLICY_REASON_PATH"]).read_text()

cose_path = pathlib.Path(sys.argv[-1])
policy_action_path = cose_path.with_suffix(".policy." + os.environ["POLICY_ACTION"].lower())
policy_action_path.write_text(policy_reason)
```

Simple drop rule based on claim content allowlist.

**allowlist.schema.json**

```json
{
    "$id": "https://schema.example.com/scitt-allowlist.schema.json",
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "properties": {
        "issuer": {
            "type": "string",
            "enum": [
                "did:web:example.org"
            ]
        }
    }
}
```

**jsonschema_validator.py**

```python
import os
import sys
import json
import pathlib
import unittest
import traceback
import contextlib
import urllib.parse

import jwt
import cwt
import cwt.algs.ec2
import cbor2
import pycose

# TODO Remove this once we have a example flow for proper key verification
import jwcrypto.jwk
from jsonschema import validate, ValidationError
import pycose.keys.ec2
import cryptography.hazmat.primitives.serialization
from pycose.messages import Sign1Message

from scitt_emulator.scitt import ClaimInvalidError, CWTClaims

claim = sys.stdin.buffer.read()

msg = Sign1Message.decode(claim, tag=True)

if pycose.headers.ContentType not in msg.phdr:
    raise ClaimInvalidError("Claim does not have a content type header parameter")

if not msg.phdr[pycose.headers.ContentType].startswith("application/json"):
    raise TypeError(
        f"Claim content type does not start with application/json: {msg.phdr[pycose.headers.ContentType]!r}"
    )

# TODO Whatever the opisite of COSESign1 is

# Figure out what the issuer is
cwt_cose_loads = cwt.cose.COSE()._loads
cwt_unverified_protected = cwt_cose_loads(cwt_cose_loads(msg.phdr[CWTClaims]).value[2])
unverified_issuer = cwt_unverified_protected[1]

def did_web_to_url(did_web_string, scheme=os.environ.get("DID_WEB_ASSUME_SCHEME", "https")):
    return "/".join(
        [
            f"{scheme}:/",
            *[urllib.parse.unquote(i) for i in did_web_string.split(":")[2:]],
        ]
    )

if unverified_issuer.startswith("did:web:"):
    unverified_issuer = did_web_to_url(unverified_issuer)

# TODO Should we use audiance? I think no, just want to make sure we've
# documented why thought if not. No usage makes sense to me becasue we don't
# know the intended audiance, it could be federated into multiple TS

# TODO Can you just pass a whole public key as an issuer?

# Load keys from issuer
jwk_keys = []

import urllib.request
import urllib.parse

# TODO did:web: -> URL
from cryptography.hazmat.primitives import serialization

cryptography_ssh_keys = []
if "://" in unverified_issuer and not unverified_issuer.startswith("file://"):
    # TODO Logging for URLErrors
    # Check if OIDC issuer
    unverified_issuer_parsed_url = urllib.parse.urlparse(unverified_issuer)
    openid_configuration_url = unverified_issuer_parsed_url._replace(
        path="/.well-known/openid-configuration",
    ).geturl()
    with contextlib.suppress(urllib.request.URLError):
        with urllib.request.urlopen(openid_configuration_url) as response:
            if response.status == 200:
                openid_configuration = json.loads(response.read())
                jwks_uri = openid_configuration["jwks_uri"]
                with urllib.request.urlopen(jwks_uri) as response:
                    if response.status == 200:
                        jwks = json.loads(response.read())
                        for jwk_key_as_dict in jwks["keys"]:
                            jwk_key_as_string = json.dumps(jwk_key_as_dict)
                            jwk_keys.append(
                                jwcrypto.jwk.JWK.from_json(jwk_key_as_string),
                            )

    # Try loading ssh keys. Example: https://github.com/username.keys
    with contextlib.suppress(urllib.request.URLError):
        with urllib.request.urlopen(unverified_issuer) as response:
            while line := response.readline():
                with contextlib.suppress(
                    (ValueError, cryptography.exceptions.UnsupportedAlgorithm)
                ):
                    cryptography_ssh_keys.append(
                        cryptography.hazmat.primitives.serialization.load_ssh_public_key(
                            line
                        )
                    )

for cryptography_ssh_key in cryptography_ssh_keys:
    jwk_keys.append(
        jwcrypto.jwk.JWK.from_pem(
            cryptography_ssh_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
    )

cwt_cose_keys = []
pycose_cose_keys = []

for jwk_key in jwk_keys:
    cwt_cose_key = cwt.COSEKey.from_pem(
        jwk_key.export_to_pem(),
        kid=jwk_key.thumbprint(),
    )
    cwt_cose_keys.append(cwt_cose_key)
    cwt_ec2_key_as_dict = cwt_cose_key.to_dict()
    pycose_cose_key = pycose.keys.ec2.EC2Key.from_dict(cwt_ec2_key_as_dict)
    pycose_cose_keys.append(pycose_cose_key)

verify_signature = False
for pycose_cose_key in pycose_cose_keys:
    with contextlib.suppress(Exception):
        msg.key = pycose_cose_key
        verify_signature = msg.verify_signature()
        if verify_signature:
            break

unittest.TestCase().assertTrue(
    verify_signature,
    "Failed to verify signature on statement",
)

cwt_protected = cwt.decode(msg.phdr[CWTClaims], cwt_cose_keys)
issuer = cwt_protected[1]
subject = cwt_protected[2]

# TODO Validate content type is JSON?
SCHEMA = json.loads(pathlib.Path(os.environ["SCHEMA_PATH"]).read_text())

try:
    validate(
        instance={
            "$schema": "https://schema.example.com/scitt-policy-engine-jsonschema.schema.json",
            "issuer": issuer,
            "subject": subject,
            "claim": json.loads(msg.payload.decode()),
        },
        schema=SCHEMA,
    )
except ValidationError as error:
    print(str(error), file=sys.stderr)
    sys.exit(1)
```

We'll create a small wrapper to serve in place of a more fully featured policy
engine.

**policy_engine.sh**

```bash
export SCHEMA_PATH="${1}"
CLAIM_PATH="${2}"

echo ${CLAIM_PATH}

(python3 jsonschema_validator.py < ${CLAIM_PATH} 2>error && POLICY_ACTION=insert python3 enforce_policy.py ${CLAIM_PATH}) || (python3 -c 'import sys, json; print(json.dumps({"type": "denied", "detail": sys.stdin.read()}))' < error > reason.json; POLICY_ACTION=denied POLICY_REASON_PATH=reason.json python3 enforce_policy.py ${CLAIM_PATH})
```

Example running allowlist check and enforcement.

```console
$ npm install nodemon && \
  node_modules/.bin/nodemon -e .cose --exec 'find workspace/storage/operations -name \*.cose -exec nohup sh -xe policy_engine.sh $(cat workspace/service_parameters.json | jq -r .insertPolicy) {} \;'
```

Also ensure you restart the server with the new config we edited.

```console
$ scitt-emulator server --workspace workspace/ --tree-alg CCF --use-lro
```

The current emulator notary (create-statement) implementation will sign
statements using a generated key or a key we provide via the `--private-key-pem`
argument. If we provide the `--private-key-pem` argument but the key at the
given path does not exist, the generated key will be written out to that path.

```console
$ export ISSUER_PORT="9000" && \
  export ISSUER_URL="http://localhost:${ISSUER_PORT}"
$ scitt-emulator client create-claim \
    --private-key-pem private-key.pem \
    --issuer "${ISSUER_URL}" \
    --subject "solar" \
    --content-type application/json \
    --payload '{"sun": "yellow"}' \
    --out claim.cose
```

The core of policy engine we implemented in `jsonschema_validator.py` will
verify the COSE message generated using the public portion of the notary's key.
We've implemented two possible styles of key resolution. Both of them require
resolution of public keys via an HTTP server.

Let's start the HTTP server now, we'll populate the needed files in the
sections corresponding to each resolution style.

```console
$ python -m http.server "${ISSUER_PORT}" &
$ python_http_server_pid=$!
```

### SSH `authorized_keys` style notary public key resolution

Keys are discovered via making an HTTP GET request to the URL given by the
`issuer` parameter via the `web` DID method and de-serializing the SSH
public keys found within the response body.

Start an HTTP server with an SSH public key served at the root.

```console
$ cat private-key.pem | ssh-keygen -f /dev/stdin -y | tee index.html
```

### OpenID Connect token style notary public key resolution

Keys are discovered two part resolution of HTTP paths relative to the issuer

`/.well-known/openid-configuration` path is requested via HTTP GET. The
response body is parsed as JSON and the value of the `jwks_uri` key is
requested via HTTP GET.

`/.well-known/jwks` (is typically the value of `jwks_uri`) path is requested
via HTTP GET. The response body is parsed as JSON. Public keys are loaded
from the value of the `keys` key which stores an array of JSON Web Key (JWK)
style serializations.

```console
$ mkdir -p .well-known/
$ cat > .well-known/openid-configuration <<EOF
{
    "issuer": "${ISSUER_URL}",
    "jwks_uri": "${ISSUER_URL}/.well-known/jwks",
    "response_types_supported": ["id_token"],
    "claims_supported": ["sub", "aud", "exp", "iat", "iss"],
    "id_token_signing_alg_values_supported": ["ES384"],
    "scopes_supported": ["openid"]
}
EOF
$ cat private-key.pem | python -c 'import sys, json, jwcrypto.jwt; key = jwcrypto.jwt.JWK(); key.import_from_pem(sys.stdin.buffer.read()); print(json.dumps({"keys":[{**key.export_public(as_dict=True),"use": "sig","kid": key.thumbprint()}]}, indent=4, sort_keys=True))' | tee .well-known/jwks
{
    "keys": [
        {
            "crv": "P-384",
            "kid": "y96luxaBaw6FeWVEMti_iqLWPSYk8cKLzZG8X45PA2k",
            "kty": "EC",
            "use": "sig",
            "x": "ZQazDzYmcMHF5Dstkbw7SwWvR_oXQHFS-TLppri-0xDby8TmCpzHyr6TH03CLBxj",
            "y": "lsIbRskEv06Rf0vttkB3vpXdZ-a50ck74MVyRwOvN55P4s8usQAm3PY1KnAgWtHF"
        }
    ]
}
```

Attempt to submit the statement we created. You should see that due to our
current `allowlist.schema.json` the Transparency Service denied the insertion
of the statement into the log.

```console
$ scitt-emulator client submit-claim --claim claim.cose --out claim.receipt.cbor
Traceback (most recent call last):
  File "/home/alice/.local/bin/scitt-emulator", line 33, in <module>
    sys.exit(load_entry_point('scitt-emulator', 'console_scripts', 'scitt-emulator')())
  File "/home/alice/Documents/python/scitt-api-emulator/scitt_emulator/cli.py", line 22, in main
    args.func(args)
  File "/home/alice/Documents/python/scitt-api-emulator/scitt_emulator/client.py", line 196, in <lambda>
    func=lambda args: submit_claim(
  File "/home/alice/Documents/python/scitt-api-emulator/scitt_emulator/client.py", line 107, in submit_claim
    raise_for_operation_status(operation)
  File "/home/alice/Documents/python/scitt-api-emulator/scitt_emulator/client.py", line 43, in raise_for_operation_status
    raise ClaimOperationError(operation)
scitt_emulator.client.ClaimOperationError: Operation error denied: 'did:web:example.com' is not one of ['did:web:example.org']

Failed validating 'enum' in schema['properties']['issuer']:
    {'enum': ['did:web:example.org'], 'type': 'string'}

On instance['issuer']:
    'did:web:example.com'
```

Modify the allowlist to ensure that our issuer, aka our local HTTP server with
our keys, is set to be the allowed issuer.

```console
$ export allowlist="$(cat allowlist.schema.json)" && \
    jq '.properties.issuer.enum[0] = env.ISSUER_URL' <(echo "${allowlist}") \
    | tee allowlist.schema.json
```

Submit the statement from the issuer we just added to the allowlist.

```console
$ scitt-emulator client submit-claim --claim claim.cose --out claim.receipt.cbor
Claim registered with entry ID 1
Receipt written to claim.receipt.cbor
```

Stop the server that serves the public keys

```console
$ kill $python_http_server_pid
```

### Binding Notary Keys to a Trusted Platform Module

Check if you have a TPM and if it's TPM2

```echo
$ echo TPM version $(cat /sys/class/tpm/tpm*/tpm_version_major)
TPM version 2
```

Upstream:  https://github.com/tpm2-software/tpm2-pkcs11/blob/master/docs/SSH.md

Below, will be examples and discussion on how to configure SSH with tpm2-pkcs11 to ssh to
the local host. The example described here could be extended for remote ssh login as well.

We assume a machine configured in such a state where a user can ssh locally and login with
a password prompt, ala:
```sh
ssh user@127.0.0.1
user@127.0.0.1's password:
Last login: Thu Sep  6 12:23:07 2018 from 127.0.0.1
```
works.

**Thus we assume a working ssh server, client and ssh-keygen services and utilities are present.**

#### Step 1 - Initializing a Store

Start by reading the document on initialization [here](INITIALIZING.md). Only brief commands
will be provided here, so a basic understanding of the initialization process is paramount.

We start by creating a tpm2-pkcs11 *store* and set up an RSA2048 key that SSH can used.
**Note**: Most SSH configurations allow RSA2048 keys to be used, but this can be turned off
  in the config, but this is quite rare.

```bash
tpm2_ptool.py init --path=~/tmp

tpm2_ptool.py addtoken --pid=1 --label=label --sopin=mysopin --userpin=myuserpin --path=~/tmp

tpm2_ptool.py addkey --algorithm=rsa2048 --label=label --userpin=myuserpin --path=~/tmp
```

#### Step 2 - Exporting the Store

Since we didn't use the default store location by setting `--path` in the `tpm2-ptool` tool, we must export the
store so the library can find it. We do this via:
```sh
export TPM2_PKCS11_STORE=$HOME/tmp
```

**Note**: The tpm2-pkcs11.so library *WILL NOT EXPAND `~`* and thus you have to use something the shell will expand,
like `$HOME`.

#### Step 3 - Generating the SSH key public portion

The next step will use `ssh-keygen` command to generate the public portion of an ssh key. The command is slightly complicated
as we use tee to redirect the output to both a file called `my.pub` and to *stdout* for viewing.

Note: You may need to update the path to the tpm2-pkcs11 shared object below.

```bash
ssh-keygen -D ./src/.libs/libtpm2_pkcs11.so | tee my.pub
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0CTmUAAB8jfNNHrw99m7K3U/+qbV1pAb7es3L+COqDh4eDqqekCm8gKHV4PFM9nW7z6CEfqzpUxYi5VvRFdYaU460bhye7NJbE0t9wjOirWtQbI6XMCKFiv/v8ThAtROT+KKYso7BK2A6spkCQwcHoaQU72C1vGouqtP5l/XRIYydp3P1wUdgQDZ8FoGhdH5dL3KnRpKR2d301GcbxMxKg5yhc/mTNkv1ZoLIcwMY7juAjzin/BhcYIDSz3sJ9C2VsX8FZXmbEo3olYU4ZfBZ+45KJ81MtWgrkXSzetwUfiH6eeTqNfqGT2IpSwDLFHTX2TsJyFDcM7Q+QR44lEU/
```

#### Step 4 - Configuring SSH to Accept the Key

Now that the public portion of the key is in ssh format and located in file `my.pub` we can add this to the `authorized_keys2` file for the user:
```bash
cat my.pub >> ~/.ssh/authorized_keys2
```

SSH consults this file and trusts private keys corresponding with the public entries.

#### Step 5 - Ensuring the Library is in a Good Path

Using the ssh client, we login. Note that ssh won't accept pkcs11 libraries outside of "trusted" locations. So we copy the PKCS\#11 library to
a trusted location. Thus you can either do `sudo make install` to move the binary to a trusted location or just do it manually.

Manual Method:
```sh
sudo cp src/.libs/libtpm2_pkcs11.so /usr/local/lib/libtpm2_pkcs11.so
```

On Ubuntu 16.04 with no configuration options specified to alter installation locations, they end up in the same location for both the *manual method*
and `sudo make install` method.

#### Step 6 - Logging In via SSH

To log in, one used the `ssh` client application and specifies the path to the PKCS11 library via the `-I` option. It will prompt for the user PIN, which
in the example is set to `myuserpin`.

```bash
ssh -I /usr/local/lib/libtpm2_pkcs11.so 127.0.0.1
Enter PIN for 'label': myuserpin
Last login: Fri Sep 21 13:28:31 2018 from 127.0.0.1
```

You are now logged in with a key resident in the TPM being exported via the tpm2-pkcs11 library.

#### TODO

- [ ] `unittest.mock.patch` the `pycose.algorithms._Ecdsa.sign` method to
  attempt usage of PKCS#11 module to sign.

```python
class _Ecdsa(CoseAlgorithm, ABC):
    @classmethod
    def sign(cls, key: 'EC2', data: bytes) -> bytes:
        sk = SigningKey.from_secret_exponent(int(hexlify(key.d), 16), curve=cls.get_curve())

        return sk.sign_deterministic(data, hashfunc=cls.get_hash_func())
```
