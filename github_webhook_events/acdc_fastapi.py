import contextlib
from typing import List, Dict

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import keri.core.coring as coring
import keri.core.serdering as serdering
import keri.app.habbing as habbing
import keri.vdr.verifying as verifying
import uvicorn

# Define FastAPI apps
app_alice = FastAPI()
app_bob = FastAPI()

import snoop


# Pydantic models for key generation options and ACDC message structure
class KeyGenerationOptions(BaseModel):
    salt: bytes = Field(
        description="Salt for key derivation",
        default_factory=lambda: b"0123456789abcdef",
    )
    passcode: bytes = Field(
        description="Passcode for key generation",
        default_factory=lambda: b"0123456789abcdef",
    )


class ACDCMessage(BaseModel):
    data: Dict
    serder: str
    sig: List[str]


# Helper function to set up a KERI identifier (used for both Alice and Bob)
@snoop
@contextlib.contextmanager
def setup_identifier(name: str, keygen_options: KeyGenerationOptions):
    with habbing.openHab(name, salt=keygen_options.salt, temp=False) as (hby, hab):
        yield hab


# Alice's endpoint to send an ACDC message to Bob
@app_alice.post("/alice/send_acdc/")
def alice_send_acdc(acdc: ACDCMessage, keygen_options: KeyGenerationOptions):
    # Setup Alice's KERI identifier with given key generation options
    with setup_identifier("alice", keygen_options) as alice_hab, setup_identifier(
        "bob", keygen_options
    ) as bob_hab:
        # Create the verifier for Bob's KERI instance
        verifier = verifying.Verifier(db=bob_hab.db)
        # Deserialize the message
        serder = serdering.Serder(raw=bytes.fromhex(acdc.serder))
        # Verify the signature
        if verifier.verify(serder.raw, acdc.sig):
            return {"status": "ACDC verified by Bob"}
        else:
            raise HTTPException(status_code=400, detail="ACDC verification failed")


# Bob's endpoint to receive and verify an ACDC message
@app_bob.post("/bob/receive_acdc/")
def bob_receive_acdc(acdc: ACDCMessage, keygen_options: KeyGenerationOptions):
    # Setup Bob's KERI identifier with given key generation options
    with setup_identifier("alice", keygen_options) as alice_hab, setup_identifier(
        "bob", keygen_options
    ) as bob_hab:
        # Create the verifier for Alice's KERI instance
        verifier = verifying.Verifier(db=alice_hab.db)
        # Deserialize the message
        serder = serdering.Serder(raw=bytes.fromhex(acdc.serder))
        # Verify the signature
        if verifier.verify(serder.raw, acdc.sig):
            return {"status": "ACDC verified by Alice"}
        else:
            raise HTTPException(status_code=400, detail="ACDC verification failed")


# Example test scenario where Alice sends ACDC to Bob
def test_alice_bob_exchange():
    keygen_options = KeyGenerationOptions(
        salt=b"0123456789abcdef",
        passcode=b"0123456789abcdef",
    )

    # Setup Alice's identifier
    with setup_identifier("alice", keygen_options) as alice_hab:
        # Create a sample message
        data = {"message": "Hello from Alice"}
        serder = serdering.Serder(raw=data)  # Serialize the data
        sig = alice_hab.mgr.sign(serder.raw, alice_hab.pre)
        # Alice sends ACDC message to Bob
        acdc_message = ACDCMessage(
            data=data, serder=serder.raw.hex(), sig=[s.qb64 for s in sig]
        )

    snoop.pp(acdc_message, keygen_options)

    # Send the message to Bob via the FastAPI endpoint
    response = app_bob.test_client().post(
        "/bob/receive_acdc/",
        json=acdc_message.dict(),
        params={"keygen_options": keygen_options.dict()},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ACDC verified by Alice"


if __name__ == "__main__":
    uvicorn.run(app_alice, host="127.0.0.1", port=8000)
    uvicorn.run(app_bob, host="127.0.0.1", port=8001)
