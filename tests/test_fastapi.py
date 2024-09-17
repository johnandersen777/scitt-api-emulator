from acdc_fastapi.app import *

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
