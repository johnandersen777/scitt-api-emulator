# SCITT Federation via ActivityPub POC

> Using bovine Python package

- Prep for OpenVEX meeting tomorrow
  - Objective: Minimal SCITT payload of VEX broadcast over ActivityPub
- https://codeberg.org/bovine/bovine/src/branch/main/bovine_herd/FEDERATION.md
  - https://www.darkreading.com/cloud/-cattle-not-pets-the-rise-of-security-as-code
  - https://zitadel.com/docs/blog/treat-clusters-as-cattle
    - > ![clusters-are-cattle-not-pets](https://github.com/intel/dffml/assets/5950433/77d2673f-ed5f-4202-bb44-25f76060f45f)
- https://codeberg.org/bovine/bovine
  - Most of the tools need to be run from the directory with the SQLite database in them (`bovine.sqlite3`)
- https://bovine-herd.readthedocs.io/en/latest/deployment.html
  - Bovine and associated libraries **require Python 3.11 or greater!!!**

```console
$ python --version
Python 3.11.5
```

```console
python -m venv .venv && \
. .venv/bin/activate && \
pip install -U pip setuptools wheel && \
pip install \
  toml \
  bovine{-store,-process,-pubsub,-herd,-tool} \
  'https://codeberg.org/pdxjohnny/bovine/archive/activitystreams_collection_helper_enable_multiple_iterations.tar.gz#egg=bovine&subdirectory=bovine' \
  'https://codeberg.org/pdxjohnny/mechanical_bull/archive/event_loop_on_connect_call_handlers.tar.gz#egg=mechanical-bull'
```

```python
from quart import Quart

from bovine_herd import BovineHerd
from bovine_pubsub import BovinePubSub

app = Quart(__name__)
BovinePubSub(app)
BovineHerd(app)
```

```console
$ hypercorn app:app
```

- https://blog.mymath.rocks/2023-03-25/BIN2_Moo_Client_Registration_Flow
- https://codeberg.org/bovine/bovine/src/branch/main/bovine_store/bovine_store/actor/test_register.py
- We need to register a user first
- https://codeberg.org/bovine/bovine/src/branch/main/bovine_tool

```console
$ export HANDLE_NAME=alice
$ export BOVINE_NAME=$(python -m bovine_tool.register "${HANDLE_NAME}" --domain http://localhost:8000 | awk '{print $NF}')
$ echo $BOVINE_NAME
alice_80cde26c-e4a7-4941-95ed-77cf8af14810
$ sqlite3 bovine.sqlite3 "SELECT * FROM bovineactor;"
1|__bovine__application_actor__|bovine|{}|2023-10-15 18:37:25.678942+00:00|2023-10-15 18:37:25.678976+00:00
2|alice_b0412432-cdb6-44d5-8789-b9fcf0cd04bc|alice|{}|2023-10-15 19:12:17.408055+00:00|2023-10-15 19:12:17.408070+00:00
$ sqlite3 bovine.sqlite3 "SELECT * FROM sqlite_master WHERE type='table';"
$ curl -s "http://localhost:8000/.well-known/webfinger?resource=acct:${HANDLE_NAME}@localhost:8000" | jq
```

```json
{
  "links": [
    {
      "href": "http://localhost:8000/endpoints/IlCKASjVegMJEKtNg_JLmmMQjJksrjnTEJH_xvmrvjY",
      "rel": "self",
      "type": "application/activity+json"
    }
  ],
  "subject": "acct:alice@localhost:8000"
}
```

- https://bovine.readthedocs.io/en/latest/tutorial_client.html
  - https://codeberg.org/bovine/mechanical_bull
    - We can use the client APIs via the mechanical-bull library's abstraction.
      - https://codeberg.org/bovine/mechanical_bull/src/branch/main/examples/moocow_handler.py
    - We first generate a config file (`config.toml`) for the user we which to automate actions for.
    - Add user with `--accept` to automate the accepting of follow requests.

```console
$ python -m mechanical_bull.add_user --accept "${HANDLE_NAME}" http://localhost:8000
Adding new user to config.toml
Please add did:key:z6MkeygVtzoxnLjWBewVr1PspbqqfvzURsE5e4ipsjxFJ8px to the access list of your ActivityPub actor
```

```toml
[alice]
secret = "z3u2U84hz8wxvB29HKwDhadxAKLxfv65qSNfYTK6vedzH9fn"
host = "http://localhost:8000"

[alice.handlers]
"mechanical_bull.actions.accept_follow_request" = true
```

- https://bovine-store.readthedocs.io/en/latest/reference/bovine_store.html#bovine_store.BovineAdminStore.add_identity_string_to_actor
  - > This will create the account @moocow@cows.example which can be accessed through Moo-Auth-1 with the secret corresponding to the did.
  - > Modifies an Actor by adding a new identity to it. name is used to identity the identity and serves little functional purpose.
  - Future ref SCITT DID
- https://codeberg.org/bovine/bovine/src/branch/main/bovine_tool#managing-users
  - The `bovine_tool.manage` command which we use to add dids to a user takes the `bovine_name`, the unique name for a user within the DB, NOT the handle.
  - https://codeberg.org/bovine/bovine/src/commit/5967146abbdd0b1f7a11f56336f8fe8fcd2b87e8/bovine_store/bovine_store/models.py#L60

```console
$ sqlite3 -csv -header bovine.sqlite3 "SELECT * FROM sqlite_master WHERE type='table' AND name='bovineactor';"
```

```csv
type,name,tbl_name,rootpage,sql
table,bovineactor,bovineactor,2,"CREATE TABLE ""bovineactor"" (
    ""id"" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    ""bovine_name"" VARCHAR(255) NOT NULL UNIQUE,
    ""handle_name"" VARCHAR(255) NOT NULL,
    ""properties"" JSON NOT NULL,
    ""created"" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    ""last_sign_in"" TIMESTAMP NOT NULL  DEFAULT CURRENT_TIMESTAMP
)"
```

- If you are looking up the handle from a config you can run the following. Otherwise you will have gotten the `bovine_name` from `bovine_tool.register`.

```bash
export HANDLE_NAME=$(cat config.toml | python -c 'import sys, tomllib; print(list(tomllib.load(sys.stdin.buffer).keys())[0])')
export BOVINE_NAME=$(sqlite3 -csv bovine.sqlite3 "SELECT bovine_name FROM bovineactor WHERE handle_name='${HANDLE_NAME}';")
```

- Let's add that key so mechanical bull can start accepting follow requests
  - We need to add the public portion of the key, be sure to convert from the private form if you extract from the `toml` file.

```console
$ python -m bovine_tool.manage "${BOVINE_NAME}" --did_key key0 $(cat config.toml | python -c 'import sys, tomllib, bovine.crypto; print(bovine.crypto.private_key_to_did_key(tomllib.load(sys.stdin.buffer)[sys.argv[-1]]["secret"]))' "${HANDLE_NAME}")
$ sqlite3 -header -csv bovine.sqlite3 "SELECT * FROM bovineactorkeypair WHERE name='key0';" 
id,name,private_key,public_key,bovine_actor_id
4,key0,"",did:key:did:key:z6MkeyGwWnSn1DFxm48HJ6L7j9m1vxYniEseGRY46fKHu6v4,1
```

- Within the file `scitt_handler.py` we've defined our demo handler
  - We need to enable it within the mechanical bull config file (`config.toml`)
    before we run mechanical bull.

```console
$ python -c 'import sys, pathlib, toml; path = pathlib.Path(sys.argv[-3]); obj = toml.loads(path.read_text()); obj[sys.argv[-2]]["handlers"][sys.argv[-1]] = True; path.write_text(toml.dumps(obj))' config.toml "${HANDLE_NAME}" scitt_handler
```

- Now we run the automations for our client actor (Alice) via mechanical bull.

```console
$ PYTHONPATH=$PYTHONPATH:$PWD python -m mechanical_bull.run
INFO:mechanical_bull.event_loop:Connected
INFO:root:/home/pdxjohnny/Documents/fediverse/bovine/hacking/scitt_handler.py:handle(handler_event=HandlerEvent.OPENED)
client: BovineClient(actor_id='http://localhost:8000/endpoints/KUMjPaGP8Ei1eXoy3udib5uLirzABP8YqAdD8yysrDI', public_key_url=None, access_token=None, secret='z3u2aZCG3JJQrsn7fcH9ZeRrod6NGUBdbWnptgYFsQtXWVXy', domain='http://localhost:8000', client=<bovine.clients.moo_auth.MooAuthClient object at 0x7f3f59907350>, session=<aiohttp.client.ClientSession object at 0x7f3f5b0a0f90>)
outbox: <bovine.activitystreams.collection_helper.CollectionHelper object at 0x7f3f5a5065d0>
Begin iteration 0 over outbox
End iteration 0 over outbox
No messages in outbox, creating activity
creating activity: {'@context': 'https://www.w3.org/ns/activitystreams', 'type': 'Announce', 'actor': 'http://localhost:8000/endpoints/KUMjPaGP8Ei1eXoy3udib5uLirzABP8YqAdD8yysrDI', 'to': ['https://www.w3.org/ns/activitystreams#Public'], 'cc': ['http://localhost:8000/endpoints/aT4gehUFZzgc1sf_UNosuO-Fyle1eN2D6NBLviXMtzs']}
created activity: {'@context': 'https://www.w3.org/ns/activitystreams', 'type': 'Announce', 'actor': 'http://localhost:8000/endpoints/KUMjPaGP8Ei1eXoy3udib5uLirzABP8YqAdD8yysrDI', 'to': ['https://www.w3.org/ns/activitystreams#Public'], 'cc': ['http://localhost:8000/endpoints/aT4gehUFZzgc1sf_UNosuO-Fyle1eN2D6NBLviXMtzs']}
Begin iteration 1 over outbox
Iteration 1 Message 1 in outbox: {'@context': 'about:bovine', 'actor': {'id': 'http://localhost:8000/endpoints/KUMjPaGP8Ei1eXoy3udib5uLirzABP8YqAdD8yysrDI', 'inbox': 'http://localhost:8000/endpoints/qGqejyzZnUBXL5vpPh5MKlXW2SktpkERFBqfHnp70MQ', 'name': 'alice', 'outbox': 'http://localhost:8000/endpoints/g5PJ-7QJ58p0aMHn3h1m0SnokPPtO6myZ1otwwV0no4', 'preferredUsername': 'alice', 'publicKey': 'http://localhost:8000/endpoints/KUMjPaGP8Ei1eXoy3udib5uLirzABP8YqAdD8yysrDI#serverKey', 'type': 'Person'}, 'cc': ['http://localhost:8000/endpoints/aT4gehUFZzgc1sf_UNosuO-Fyle1eN2D6NBLviXMtzs'], 'id': 'http://localhost:8000/objects/0a8fa278-c079-421e-87f8-76bd2dfb8cf8', 'to': ['as:Public'], 'type': 'Announce'}
End iteration 1 over outbox
```

[![asciicast](https://asciinema.org/a/614553.svg)](https://asciinema.org/a/614553)

- https://bovine.readthedocs.io/en/latest/message.html
  - We'll try creating two users and sending a message. Is that the same as a post? How can we make a regular post?
  - This also uses Moo auth, ideally we use something more standard like OIDC to not rock the boat too much.
- https://codeberg.org/bovine/mechanical_bull/src/commit/a13fc7d3d04629eeb72f3b2f0fa976e52860de68/mechanical_bull/run.py#L18
  - https://docs.python.org/3/library/asyncio-task.html?highlight=taskgroup#asyncio.TaskGroup
    - New in Python 3.11
- TODO
  - [ ] Could we issue OIDC tokens off the mechanical bull manged keys?
    - It looks like `bovine.clients.bearer` is used to talk to Mastodon's API. If we wanted to make Bovine accept token auth from a client signed OIDC token we could add routes to the Herd server for the jwks
  - [ ] KCP based config for accounts
    - https://cloud.redhat.com/blog/an-introduction-to-kcp
  - [ ] https://codeberg.org/bovine/mechanical_bull/issues/13
