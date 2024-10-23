# SCITT API Emulator

> Unstable Demo Instance

## What is SCITT?

The Supply Chain Integrity, Transparency and Trust (SCITT) initiative: [https://scitt.io](https://scitt.io)

## Usage

Here are some things you can do with this instance (which is wiped periodically)

- Follow subjects (feeds)
  - TODO Implement subjects as ActivityPub Actors
  - Follow the `demo` Actor to get events for all statements were a receipt was
    created from this Transparency Service.
- Submit Statements
- Retrieve Statements
- Retrieve Receipts

For more examples see

- [https://github.com/scitt-community/scitt-api-emulator/tree/main/docs/](https://github.com/scitt-community/scitt-api-emulator/tree/main/docs/)
- [https://github.com/scitt-community/scitt-examples/](https://github.com/scitt-community/scitt-examples)

## Federation via ActivityPub

- Federation of SCITT events enables near real-time communication between supply
  chains.
    - Acceptance of claims to SCITT where payload data contains VEX, CSAF, VSA,
      SBOM, VDR, VRF, S2C2F alignment attestations, etc. has the side effect of
      enabling a consistent pattern for notification of new vulnerability
      and other Software Supply Chain Security data.

> Below links to recording of IETF 118 SCITT Meeting, Corresponding asciinema link: [https://asciinema.org/a/619517](https://asciinema.org/a/619517)

[![asciicast-federation-activitypub-bovine](https://asciinema.org/a/619517.svg)](https://www.youtube.com/watch?v=zEGob4oqca4&t=5354s)

**workspace_federation/config.json**

```json
{
  "handle_name": "myhandle",
  "fqdn": "scitt.myhandle.example.com",
  "workspace": "/home/username/workspace_federation/",
  "bovine_db_url": "sqlite:///home/username/workspace_federation/bovine.sqlite3",
  "following": {
    "demo-unstable": {
      "actor_id": "demo@scitt.unstable.chadig.com"
    }
  }
}
```
