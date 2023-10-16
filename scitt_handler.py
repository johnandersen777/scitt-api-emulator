import bovine
import random
import json
import pprint
import logging

from mechanical_bull.handlers import HandlerEvent, HandlerAPIVersion

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def build_content(message, min_o, max_o):
    if "help" in message:
        content = """Use bold, italic for text to in bold and italic.<br/>
Use list for a list, use number for an ordered list.<br/>
Use code to include a code block<br/>
Use quote to include a quote<br/>
Use private to send the message privately<br/>
Use article to send the message as an article<br/>
Use help to see this message"""
    else:
        content = "m" + "o" * random.randint(min_o, max_o)

    if "bold" in message:
        content = f"<b>{content}</b>"

    if "italic" in message:
        content = f"<i>{content}</i>"

    if "list" in message:
        content = f"<ul><li>{content}</li></ul>"

    if "number" in message:
        content = f"<ol><li>{content}</li></ol>"

    if "code" in message:
        moo = "m" + "o" * random.randint(min_o, max_o)
        content += f"""<pre><code>print("{moo}")</code></pre>"""

    return content


async def handle(
    client: bovine.BovineClient,
    data: dict,
    min_o=4,
    max_o=20,
    handler_event: HandlerEvent = None,
    handler_api_version: HandlerAPIVersion = HandlerAPIVersion.unstable,
):
    logging.info(f"{__file__}:handle(handler_event={handler_event})")
    match handler_event:
        case HandlerEvent.OPENED:
            # TODO Channel to communicate / recv events for publish from SCITT
            # asyncio.create_task(watch_for_scitt_events())
            # The following example is from: https://codeberg.org/bovine/mechanical_bull/src/commit/a13fc7d3d04629eeb72f3b2f0fa976e52860de68/mechanical_bull/actions/announce.py#L58
            print("client:", client)
            outbox = client.outbox()
            print("outbox:", outbox)

            """
            outbox_as_collection = await outbox.as_collection()
            print("outbox_as_collection:", repr(outbox_as_collection))
            print("type(outbox_as_collection):", type(outbox_as_collection))
            print("len(outbox_as_collection.items):", len(outbox_as_collection["items"]))
            if not outbox_as_collection["items"]:
                activity = client.activity_factory.announce({}).as_public().build()
                print("creating activity:", activity)
                await client.send_to_outbox(activity)
                print("created activity:", activity)
            count_messages = 0
            print("Begin iteration over outbox_as_collection")
            for message in outbox_as_collection["items"]:
                count_messages += 1
                print(f"Message {count_messages} in outbox_as_collection:", message)
            print("End iteration over outbox_as_collection")
            """

            for i in range(0, 2):
                print(f"Begin iteration {i} over outbox")
                count_messages = 0
                async for message in outbox:
                    count_messages += 1
                    print(f"Iteration {i} Message {count_messages} in outbox:", message)
                print(f"End iteration {i} over outbox")
                # NOTE Is this a bovine bug? We have to create a new instance of
                # the outbox in order to iterate over it again. If we don't then
                # any iteration after the first round through the loop don't
                # have any prints in the body above
                # outbox = client.outbox()
            return
        case HandlerEvent.CLOSED:
            return
        case HandlerEvent.DATA:
            pprint.pprint(data)
    try:
        if data.get("type") != "Create":
            return

        obj = data.get("object")
        if not isinstance(obj, dict):
            return

        tags = obj.get("tag")
        if not isinstance(tags, list):
            if isinstance(tags, dict):
                tags = [tags]
            else:
                return

        actor_id = client.information["id"]

        def mentions_me(entry):
            return entry["type"] == "Mention" and entry["href"] == actor_id

        if not any(mentions_me(x) for x in tags):
            return

        mention = await client.object_factory.mention_for_actor_uri(obj["attributedTo"])

        if "content" in obj:
            message = obj.get("content").lower()
        else:
            message = list(obj.get("contentMap").values())[0].lower()

        content = build_content(message, min_o, max_o)

        if "private" in message:
            note = client.object_factory.note(
                content=content,
                to={obj["attributedTo"]},
                tag=[mention.build()],
                in_reply_to=obj["id"],
            ).build()
        else:
            note = (
                client.object_factory.note(
                    content=content,
                    to={obj["attributedTo"]},
                    tag=[mention.build()],
                    in_reply_to=obj["id"],
                )
                .as_public()
                .build()
            )

        if "article" in message:
            note["type"] = "Article"

        if "quote" in message:
            note[
                "content"
            ] += """<p><a href="https://mitra.social/post/0187de86-69d2-cf3b-d971-1dbb0ab5a096">https://mitra.social/post/0187de86-69d2-cf3b-d971-1dbb0ab5a096</a></p>"""
            note["tag"].append(
                {
                    "href": "https://mitra.social/post/0187de86-69d2-cf3b-d971-1dbb0ab5a096",
                    "mediaType": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
                    "rel": "https://misskey-hub.net/ns#_misskey_quote",
                    "type": "Link",
                }
            )

        logger.info("Sending...")
        logger.info(json.dumps(data))

        await client.send_to_outbox(client.activity_factory.create(note).build())
    except Exception as ex:
        logger.error(ex)
        logger.exception(ex)
        logger.error(json.dumps(data))
