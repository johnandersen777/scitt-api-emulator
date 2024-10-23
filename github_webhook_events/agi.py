import abc
import sys
import pdb
import enum
import uuid
import pprint
import asyncio
import getpass
import pathlib
import argparse
import contextlib
import dataclasses
from typing import Any, NewType, AsyncIterator

import openai
import keyring


class AGIEventType(enum.Enum):
    NEW_AGENT_CREATED = enum.auto()
    EXISTING_AGENT_RETRIEVED = enum.auto()
    NEW_CHAT_STREAM_CREATED = enum.auto()
    NEW_CHAT_STREAM_DELTA_CONTENT = enum.auto()


@dataclasses.dataclass
class AGIEvent:
    event_type: AGIEventType
    event_data: Any


class AGIActionType(enum.Enum):
    INGEST_FILE = enum.auto()
    ASK_QUESTION = enum.auto()


@dataclasses.dataclass
class AGIAction:
    action_type: AGIEventType
    action_data: Any


AGIActionStream = NewType("AGIActionStream", AsyncIterator[AGIAction])


class _KV_STORE_DEFAULT_VALUE:
    pass


KV_STORE_DEFAULT_VALUE = _KV_STORE_DEFAULT_VALUE()


class KVStore(abc.ABC):
    @abc.abstractmethod
    async def get(self, key, default_value: Any = KV_STORE_DEFAULT_VALUE):
        raise NotImplementedError()

    @abc.abstractmethod
    async def set(self, key, value):
        raise NotImplementedError()

    async def __aenter__(self):
        return self

    async def __aexit__(self, _exc_type, _exc_value, _traceback):
        return


class KVStoreKeyring(KVStore):
    def __init__(self, config):
        self.service_name = config["service_name"]

    async def get(self, key, default_value: Any = KV_STORE_DEFAULT_VALUE):
        if default_value is KV_STORE_DEFAULT_VALUE:
            return self.keyring_get_password_or_return(
                self.service_name, key, not_found_return_value=default_value
            )
        return keyring.get_password(self.service_name, key)

    async def set(self, key, value):
        return keyring.set_password(self.service_name, key, value)

    @staticmethod
    def keyring_get_password_or_return(
        service_name: str,
        username: str,
        not_found_return_value=None,
    ) -> str:
        with contextlib.suppress(Exception):
            return keyring.get_password(service_name, username)
        return not_found_return_value


def make_argparse_parser(argv=None):
    parser = argparse.ArgumentParser(description="LLM Based Assistant")
    parser.add_argument(
        "--agi-name",
        dest="agi_name",
        default="alice",
        type=str,
    )
    parser.add_argument(
        "--kvstore-service-name",
        dest="kvstore_service_name",
        default="alice",
        type=str,
    )
    parser.add_argument(
        "--openai-api-key",
        dest="openai_api_key",
        type=str,
        default=KVStoreKeyring.keyring_get_password_or_return(
            getpass.getuser(),
            "openai.api.key",
        ),
        help="OpenAI API Key",
    )

    return parser


import inspect
import asyncio
from collections import UserList
from contextlib import AsyncExitStack
from typing import (
    Dict,
    Any,
    AsyncIterator,
    Tuple,
    Type,
    AsyncContextManager,
    Optional,
    Set,
)


async def concurrently(
    work: Dict[asyncio.Task, Any],
    *,
    errors: str = "strict",
    nocancel: Optional[Set[asyncio.Task]] = None,
) -> AsyncIterator[Tuple[Any, Any]]:
    # Track if first run
    first = True
    # Set of tasks we are waiting on
    tasks = set(work.keys())
    # Return when outstanding operations reaches zero
    try:
        while first or tasks:
            first = False
            # Wait for incoming events
            done, _pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                # Remove the task from the set of tasks we are waiting for
                tasks.remove(task)
                # Get the tasks exception if any
                exception = task.exception()
                if errors == "strict" and exception is not None:
                    raise exception
                if exception is None:
                    # Remove the compeleted task from work
                    complete = work[task]
                    del work[task]
                    yield complete, task.result()
                    # Update tasks in case work has been updated by called
                    tasks = set(work.keys())
    finally:
        for task in tasks:
            if not task.done() and (nocancel is None or task not in nocancel):
                task.cancel()
            else:
                # For tasks which are done but have exceptions which we didn't
                # raise, collect their exceptions
                task.exception()


async def assistant_openai(
    tg: asyncio.TaskGroup,
    agi_name: str,
    kvstore: KVStore,
    action_stream: AGIActionStream,
    openai_api_key: str,
):
    client = openai.AsyncOpenAI(
        api_key=openai_api_key,
    )

    kvstore_key_assistant_id = f"openai.assistants.{agi_name}.id"
    assistant_id = await kvstore.get(kvstore_key_assistant_id)

    assistant = None
    if assistant_id:
        with contextlib.suppress(openai.NotFoundError):
            assistant = await client.beta.assistants.retrieve(
                assistant_id=assistant_id,
            )
            yield AGIEvent(
                event_type=AGIEventType.EXISTING_AGENT_RETRIEVED,
                event_data=assistant,
            )
    if not assistant:
        assistant = await client.beta.assistants.create(
            name=agi_name,
            instructions=pathlib.Path(__file__)
            .parent.joinpath("openai_assistant_instructions.md")
            .read_text(),
            # model="gpt-4-1106-preview",
            model=kvstore.get(
                f"openai.assistants.{agi_name}.model", "gpt-3.5-turbo-1106"
            ),
            tools=[{"type": "retrieval"}],
            # file_ids=[file.id],
        )
        await kvstore.set(kvstore_key_assistant_id, assistant.id)
        yield AGIEvent(
            event_type=AGIEventType.NEW_AGENT_CREATED,
            event_data=assistant,
        )

    action_stream_iter = action_stream.__aiter__()
    work = {
        tg.create_task(action_stream_iter.__anext__()): (
            "action_stream",
            action_stream_iter,
        ),
    }
    async for (work_name, work_ctx), result in concurrently(work):
        if work_ctx is action_stream:
            work[tg.create_task(work_ctx.__anext__())] = (work_name, work_ctx)
            if result.action_type == AGIActionType.INGEST_FILE:
                raise NotImplementedError()
            elif result.action_type == AGIActionType.ASK_QUESTION:
                stream = await client.chat.completions.create(
                    prompt="Say this is a test",
                    messages=[
                        {"role": "user", "content": "Say this is a test"}
                    ],
                    stream=True,
                )
                stream_id = str(uuid.uuid4())
                yield AGIEvent(
                    event_type=AGIEventType.NEW_CHAT_STREAM_CREATED,
                    event_data=stream_id,
                )
                chat_stream_iter = stream.__aiter__()
                work[tg.create_task(chat_stream_iter.__anext__())] = (
                    f"chat.stream.{stream_id}",
                    chat_stream_iter,
                )
        elif work_name.startswith("chat.stream."):
            _, _, stream_id = work_name.split(".", maxsplit=3)
            work[tg.create_task(work_ctx.__anext__())] = (work_name, work_ctx)
            yield AGIEvent(
                event_type=AGIEventType.NEW_CHAT_STREAM_DELTA_CONTENT,
                event_data=part.choices[0].delta.content,
            )


async def pdb_action_stream(tg):
    while True:
        yield await asyncio.to_thread(lambda: eval(input("(agi: alice) $ ")))


async def main(
    agi_name: str,
    kvstore_service_name: str,
    *,
    kvstore: KVStore = None,
    action_stream: AGIActionStream = None,
    openai_api_key: str = None,
):
    if not kvstore:
        kvstore = KVStoreKeyring({"service_name": kvstore_service_name})

    async with kvstore, asyncio.TaskGroup() as tg:
        if not action_stream:
            action_stream = pdb_action_stream(tg)

        if openai_api_key:
            assistant = assistant_openai(
                tg, agi_name, kvstore, action_stream, openai_api_key
            )
        else:
            raise Exception(
                "No API keys or implementations of assistants given"
            )

        async for assistant_event in assistant:
            pprint.pprint(assistant_event)


if __name__ == "__main__":
    parser = make_argparse_parser()

    args = parser.parse_args(sys.argv[1:])

    asyncio.run(main(**vars(args)))
