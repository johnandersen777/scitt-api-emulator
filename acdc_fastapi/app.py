import contextlib
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import keri.core.serdering as serdering
import keri.app.habbing as habbing
import keri.vdr.verifying as verifying

# Define FastAPI apps for Alice and Bob
app_alice = FastAPI()
app_bob = FastAPI()

# Pydantic models for key generation options and ACDC message structure
class KeyGenerationOptions(BaseModel):
    salt: bytes = Field(default_factory=lambda: b"0123456789abcdef", description="Salt for key derivation")
    passcode: bytes = Field(default_factory=lambda: b"0123456789abcdef", description="Passcode for key generation")

class ACDCMessage(BaseModel):
    data: Dict
    serder: str
    sig: List[str]

# Helper function to set up a KERI identifier (used for both Alice and Bob)
@contextlib.contextmanager
def setup_identifier(name: str, keygen_options: KeyGenerationOptions):
    with habbing.openHab(name, salt=keygen_options.salt, temp=False) as (hby, hab):
        yield hab

# Alice's endpoint to send an ACDC message to Bob
@app_alice.post("/alice/send_acdc/")
def alice_send_acdc(acdc: ACDCMessage, keygen_options: KeyGenerationOptions):
    with setup_identifier("alice", keygen_options) as alice_hab, setup_identifier("bob", keygen_options) as bob_hab:
        verifier = verifying.Verifier(db=bob_hab.db)
        serder = serdering.Serder(raw=bytes.fromhex(acdc.serder))
        if verifier.verify(serder.raw, acdc.sig):
            return {"status": "ACDC verified by Bob"}
        else:
            raise HTTPException(status_code=400, detail="ACDC verification failed")

# Bob's endpoint to receive and verify an ACDC message
@app_bob.post("/bob/receive_acdc/")
def bob_receive_acdc(acdc: ACDCMessage, keygen_options: KeyGenerationOptions):
    with setup_identifier("alice", keygen_options) as alice_hab, setup_identifier("bob", keygen_options) as bob_hab:
        verifier = verifying.Verifier(db=alice_hab.db)
        serder = serdering.Serder(raw=bytes.fromhex(acdc.serder))
        if verifier.verify(serder.raw, acdc.sig):
            return {"status": "ACDC verified by Alice"}
        else:
            raise HTTPException(status_code=400, detail="ACDC verification failed")
