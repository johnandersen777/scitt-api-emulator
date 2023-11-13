# Copyright (c) SCITT Authors
# Licensed under the MIT License.
import uuid
import pathlib
import argparse
from typing import Optional

import cwt
import pycose
import pycose.headers
import pycose.messages
import pycose.keys.ec2


@pycose.headers.CoseHeaderAttribute.register_attribute()
class CWTClaims(pycose.headers.CoseHeaderAttribute):
    identifier = 14
    fullname = "CWT_CLAIMS"


@pycose.headers.CoseHeaderAttribute.register_attribute()
class RegInfo(pycose.headers.CoseHeaderAttribute):
    identifier = 393
    fullname = "REG_INFO"


@pycose.headers.CoseHeaderAttribute.register_attribute()
class Receipt(pycose.headers.CoseHeaderAttribute):
    identifier = 394
    fullname = "RECEIPT"


@pycose.headers.CoseHeaderAttribute.register_attribute()
class TBD(pycose.headers.CoseHeaderAttribute):
    identifier = 395
    fullname = "TBD"


def create_claim(
    claim_path: pathlib.Path,
    issuer: str,
    subject: str,
    content_type: str,
    payload: str,
    private_key_pem_path: Optional[str] = None,
):
    # https://ietf-wg-scitt.github.io/draft-ietf-scitt-architecture/draft-ietf-scitt-architecture.html#name-signed-statement-envelope

    # Registration Policy (label: TBD, temporary: 393): A map containing
    # key/value pairs set by the Issuer which are sealed on Registration and
    # non-opaque to the Transparency Service. The key/value pair semantics are
    # specified by the Issuer or are specific to the CWT_Claims iss and
    # CWT_Claims sub tuple.
    # Examples: the sequence number of signed statements
    # on a CWT_Claims Subject, Issuer metadata, or a reference to other
    # Transparent Statements (e.g., augments, replaces, new-version, CPE-for)
    # Reg_Info = {
    reg_info = {
        #   ? "register_by": uint .within (~time),
        "register_by": 1000,
        #   ? "sequence_no": uint,
        "sequence_no": 0,
        #   ? "issuance_ts": uint .within (~time),
        "issuance_ts": 1000,
        #   ? "no_replay": null,
        "no_replay": None,
        #   * tstr => any
    }
    # }

    # Create COSE_Sign1 structure
    # https://python-cwt.readthedocs.io/en/stable/algorithms.html
    alg = "ES384"
    # Create an ad-hoc key
    # oct: size(int)
    # RSA: public_exponent(int), size(int)
    # EC: crv(str) (one of P-256, P-384, P-521, secp256k1)
    # OKP: crv(str) (one of Ed25519, Ed448, X25519, X448)
    if private_key_pem_path and not private_key_pem_path.exists():
        import subprocess
        subprocess.check_call(
            [
                "bash",
                "-c",
                f"ssh-keygen -q -f /dev/stdout -t ecdsa -b 384 -N '' <<<y 2>/dev/null | python -c 'import sys; from cryptography.hazmat.primitives import serialization; print(serialization.load_ssh_private_key(sys.stdin.buffer.read(), password=None).private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()).decode().rstrip())' > {private_key_pem_path}",
            ]
        )
    private_key_pem = private_key_pem_path.read_bytes()
    import hashlib
    kid_hash = hashlib.sha384()
    kid_hash.update(private_key_pem)
    kid = kid_hash.hexdigest()
    cwt_cose_key = cwt.COSEKey.from_pem(private_key_pem, kid=kid)
    # cwt_cose_key = cwt.COSEKey.generate_ec2_key(alg=alg, kid=kid)
    import pprint
    cwt_ec2_key_as_dict = cwt_cose_key.to_dict()
    pprint.pprint(cwt_ec2_key_as_dict)
    import pprint
    import inspect
    cose_tags = {
        member.identifier: member.fullname
        for _member_name, member in inspect.getmembers(pycose.headers)
        if (
            hasattr(member, "identifier")
            and hasattr(member, "fullname")
        )
    }
    pprint.pprint(cose_tags)
    cwt_ec2_key_as_dict_labeled = {
        cose_tags.get(key, key): value
        for key, value in cwt_ec2_key_as_dict.items()
    }
    # print("cwt_ec2_key_as_dict_labeled['STATIC_KEY_ID']", cwt_ec2_key_as_dict_labeled['CRITICAL'])
    pprint.pprint(cwt_ec2_key_as_dict)
    pprint.pprint(cwt_ec2_key_as_dict_labeled)
    pycose_cose_key = pycose.keys.ec2.EC2Key.from_dict(cwt_ec2_key_as_dict)
    # pycose_cose_key.kid = cwt_ec2_key_as_dict_labeled['CRITICAL']
    # cwt_cose_key._kid = pycose_cose_key.kid
    sign1_message_key = pycose.keys.ec2.EC2Key.from_dict(cwt_ec2_key_as_dict)

    # CWT_Claims (label: 14 pending [CWT_CLAIM_COSE]): A CWT representing
    # the Issuer (iss) making the statement, and the Subject (sub) to
    # correlate a collection of statements about an Artifact. Additional
    # [CWT_CLAIMS] MAY be used, while iss and sub MUST be provided
    # CWT_Claims = {
    cwt_claims = {
        # iss (CWT_Claim Key 1): The Identifier of the signer, as a string
        # Example: did:web:example.com
        #   1 => tstr; iss, the issuer making statements,
        1: issuer,
        # sub (CWT_Claim Key 2): The Subject to which the Statement refers,
        # chosen by the Issuer
        # Example: github.com/opensbom-generator/spdx-sbom-generator/releases/tag/v0.0.13
        #   2 => tstr; sub, the subject of the statements,
        2: subject,
        #   * tstr => any
    }
    # }
    cwt_token = cwt.encode(cwt_claims, cwt_cose_key)
    print(cwt.decode(cwt_token , cwt_cose_key))

    # Protected_Header = {
    protected = {
        # algorithm (label: 1): Asymmetric signature algorithm used by the
        # Issuer of a Signed Statement, as an integer.
        # Example: -35 is the registered algorithm identifier for ECDSA with
        # SHA-384, see COSE Algorithms Registry [IANA.cose].
        #   1   => int             ; algorithm identifier,
        # https://www.iana.org/assignments/cose/cose.xhtml#algorithms
        # pycose.headers.Algorithm: "ES256",
        pycose.headers.Algorithm: getattr(cwt.enums.COSEAlgs, alg),
        # Key ID (label: 4): Key ID, as a bytestring
        #   4   => bstr            ; Key ID,
        pycose.headers.KID: kid.encode('ascii'),
        #   14  => CWT_Claims      ; CBOR Web Token Claims,
        CWTClaims: cwt_token,
        #   393 => Reg_Info        ; Registration Policy info,
        RegInfo: reg_info,
        #   3   => tstr            ; payload type
        pycose.headers.ContentType: content_type,
    }
    # }

    # Unprotected_Header = {
    unprotected = {
        #   ; TBD, Labels are temporary,
        TBD: "TBD",
        #   ? 394 => [+ Receipt]
        Receipt: None,
    }
    # }

    # https://github.com/TimothyClaeys/pycose/blob/e527e79b611f6cc6673bbb694056a7468c2eef75/pycose/messages/cosemessage.py#L84-L91
    msg = pycose.messages.Sign1Message(
        phdr=protected,
        uhdr=unprotected,
        payload=payload.encode("utf-8"),
    )

    # Sign
    msg.key = sign1_message_key
    # https://github.com/TimothyClaeys/pycose/blob/e527e79b611f6cc6673bbb694056a7468c2eef75/pycose/messages/cosemessage.py#L143
    claim = msg.encode(tag=True)
    claim_path.write_bytes(claim)


def cli(fn):
    p = fn("create-claim", description="Create a fake SCITT claim")
    p.add_argument("--out", required=True, type=pathlib.Path)
    p.add_argument("--issuer", required=True, type=str)
    p.add_argument("--subject", required=True, type=str)
    p.add_argument("--content-type", required=True, type=str)
    p.add_argument("--payload", required=True, type=str)
    p.add_argument("--private-key-pem", required=False, type=pathlib.Path)
    p.set_defaults(
        func=lambda args: create_claim(
            args.out,
            args.issuer,
            args.subject,
            args.content_type,
            args.payload,
            private_key_pem_path=args.private_key_pem,
        )
    )

    return p


def main(argv=None):
    parser = cli(argparse.ArgumentParser)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
