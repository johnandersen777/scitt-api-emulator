import os
import abc
import sys
import pdb
import enum
import uuid
import json
import pprint
import asyncio
import getpass
import pathlib
import argparse
import traceback
import contextlib
import collections
import dataclasses
from typing import Any, List, Optional, NewType, AsyncIterator

import openai
import keyring


def async_lambda(func):
    async def async_func():
        nonlocal func
        return func()

    return async_func


async def asyncio_sleep_for_then_coro(sleep_time, coro):
    await asyncio.sleep(sleep_time)
    return await coro


class AGIEventType(enum.Enum):
    ERROR = enum.auto()
    END_EVENTS = enum.auto()
    INTERNAL_RE_QUEUE = enum.auto()
    NEW_AGENT_CREATED = enum.auto()
    EXISTING_AGENT_RETRIEVED = enum.auto()
    NEW_FILE_ADDED = enum.auto()
    NEW_THREAD_CREATED = enum.auto()
    NEW_THREAD_RUN_CREATED = enum.auto()
    NEW_THREAD_MESSAGE = enum.auto()
    THREAD_MESSAGE_ADDED = enum.auto()
    THREAD_RUN_COMPLETE = enum.auto()
    THREAD_RUN_IN_PROGRESS = enum.auto()
    THREAD_RUN_EVENT_WITH_UNKNOWN_STATUS = enum.auto()


@dataclasses.dataclass
class AGIEvent:
    event_type: AGIEventType
    event_data: Any


@dataclasses.dataclass
class AGIEventNewAgent:
    agent_id: str
    agent_name: str


@dataclasses.dataclass
class AGIEventNewFileAdded:
    agent_id: str
    file_id: str


@dataclasses.dataclass
class AGIEventNewThreadCreated:
    agent_id: str
    thread_id: str


@dataclasses.dataclass
class AGIEventNewThreadRunCreated:
    agent_id: str
    thread_id: str
    run_id: str
    run_status: str


@dataclasses.dataclass
class AGIEventThreadRunComplete:
    agent_id: str
    thread_id: str
    run_id: str
    run_status: str


@dataclasses.dataclass
class AGIEventThreadRunInProgress:
    agent_id: str
    thread_id: str
    run_id: str
    run_status: str


@dataclasses.dataclass
class AGIEventThreadRunEventWithUnknwonStatus(AGIEventNewThreadCreated):
    agent_id: str
    thread_id: str
    run_id: str
    status: str


@dataclasses.dataclass
class AGIEventNewThreadMessage:
    agent_id: str
    thread_id: str
    message_role: str
    message_content_type: str
    message_content: str


@dataclasses.dataclass
class AGIEventThreadMessageAdded:
    agent_id: str
    thread_id: str
    message_id: str
    message_role: str
    message_content: str


class AGIActionType(enum.Enum):
    NEW_AGENT = enum.auto()
    INGEST_FILE = enum.auto()
    ADD_MESSAGE = enum.auto()
    NEW_THREAD = enum.auto()
    RUN_THREAD = enum.auto()


@dataclasses.dataclass
class AGIAction:
    action_type: AGIActionType
    action_data: Any


@dataclasses.dataclass
class AGIActionIngestFile:
    agent_id: str
    file_path: str


@dataclasses.dataclass
class AGIActionNewAgent:
    agent_id: str
    agent_name: str
    agent_instructions: str


@dataclasses.dataclass
class AGIActionNewThread:
    agent_id: str


@dataclasses.dataclass
class AGIActionAddMessage:
    agent_id: str
    thread_id: str
    message_role: str
    message_content: str


@dataclasses.dataclass
class AGIActionRunThread:
    agent_id: str
    thread_id: str


AGIActionStream = NewType("AGIActionStream", AsyncIterator[AGIAction])


class AGIStateType(enum.Enum):
    AGENT = enum.auto()
    THREAD = enum.auto()


@dataclasses.dataclass
class AGIState:
    state_type: AGIStateType
    state_data: Any


@dataclasses.dataclass
class AGIStateAgent:
    agent_name: str
    agent_id: str
    thread_ids: List[str] = dataclasses.field(
        default_factory=lambda: [],
    )


@dataclasses.dataclass
class AGIStateThread:
    agent_id: str
    thread_id: str
    most_recent_run_id: Optional[str] = None
    most_recent_run_status: Optional[str] = None


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
        if default_value is not KV_STORE_DEFAULT_VALUE:
            return self.keyring_get_password_or_return(
                self.service_name,
                key,
                not_found_return_value=default_value,
            )
        return keyring.get_password(self.service_name, key)

    async def set(self, key, value):
        return keyring.set_password(self.service_name, key, value)

    @staticmethod
    def keyring_get_password_or_return(
        service_name: str,
        username: str,
        *,
        not_found_return_value=None,
    ) -> str:
        with contextlib.suppress(Exception):
            value = keyring.get_password(service_name, username)
            if value is not None:
                return value
        return not_found_return_value


def make_argparse_parser(argv=None):
    parser = argparse.ArgumentParser(description="Generic AI")
    parser.add_argument(
        "--user-name",
        dest="user_name",
        type=str,
        default=KVStoreKeyring.keyring_get_password_or_return(
            getpass.getuser(),
            "profile.username",
            not_found_return_value=getpass.getuser(),
        ),
        help="Handle to address the user as",
    )
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
    parser.add_argument(
        "--openai-base-url",
        dest="openai_base_url",
        type=str,
        default=KVStoreKeyring.keyring_get_password_or_return(
            getpass.getuser(),
            "openai.api.base_url",
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


class _STOP_ASYNC_ITERATION:
    pass


STOP_ASYNC_ITERATION = _STOP_ASYNC_ITERATION()


async def ignore_stopasynciteration(coro):
    try:
        return await coro
    except StopAsyncIteration:
        return STOP_ASYNC_ITERATION


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


async def agent_openai(
    tg: asyncio.TaskGroup,
    agi_name: str,
    kvstore: KVStore,
    action_stream: AGIActionStream,
    openai_api_key: str,
    *,
    openai_base_url: Optional[str] = None,
):
    client = openai.AsyncOpenAI(
        api_key=openai_api_key,
        base_url=openai_base_url,
    )

    agents = {}
    threads = {}

    action_stream_iter = action_stream.__aiter__()
    work = {
        tg.create_task(
            ignore_stopasynciteration(action_stream_iter.__anext__())
        ): (
            "action_stream",
            action_stream_iter,
        ),
    }
    async for (work_name, work_ctx), result in concurrently(work):
        print(f"openai_agent.{work_name}", pprint.pformat(result))
        if result is STOP_ASYNC_ITERATION:
            continue
        try:
            # TODO There should be no await's here, always add to work
            if work_name == "action_stream":
                work[
                    tg.create_task(
                        ignore_stopasynciteration(work_ctx.__anext__())
                    )
                ] = (work_name, work_ctx)
                if result.action_type == AGIActionType.NEW_AGENT:
                    assistant = None
                    if result.action_data.agent_id:
                        with contextlib.suppress(openai.NotFoundError):
                            assistant = await client.beta.assistants.retrieve(
                                assistant_id=result.action_data.agent_id,
                            )
                            yield AGIEvent(
                                event_type=AGIEventType.EXISTING_AGENT_RETRIEVED,
                                event_data=AGIEventNewAgent(
                                    agent_id=assistant.id,
                                    agent_name=result.action_data.agent_name,
                                ),
                            )
                    if not assistant:
                        assistant = await client.beta.assistants.create(
                            name=result.action_data.agent_name,
                            instructions=result.action_data.agent_instructions,
                            # model="gpt-4-1106-preview",
                            model=await kvstore.get(
                                f"openai.assistants.{agi_name}.model",
                                "gpt-3.5-turbo-1106",
                            ),
                            tools=[{"type": "retrieval"}],
                            # file_ids=[file.id],
                        )
                        yield AGIEvent(
                            event_type=AGIEventType.NEW_AGENT_CREATED,
                            event_data=AGIEventNewAgent(
                                agent_id=assistant.id,
                                agent_name=result.action_data.agent_name,
                            ),
                        )
                    agents[assistant.id] = assistant
                elif result.action_type == AGIActionType.INGEST_FILE:
                    # TODO aiofile and tg.create_task
                    with open(result.action_data.file_path, "rb") as fileobj:
                        file = await client.files.create(
                            file=fileobj,
                            purpose="assistants",
                        )
                    file_ids = agents[result.action_data.agent_id].file_ids + [
                        file.id
                    ]
                    """
                    non_existant_file_ids = []
                    for file_id in file_ids:
                        try:
                            file = await openai.resources.beta.assistants.AsyncFiles(
                                client
                            ).retrieve(file_id, assistant_id=result.action_data.agent_id)
                        except openai.NotFoundError:
                            non_existant_file_ids.append(file_id)
                    for file_id in non_existant_file_ids:
                        file_ids.remove(file_id)
                    print("non_existant_file_ids", non_existant_file_ids, file_ids)
                    """
                    assistant = (
                        await openai.resources.beta.assistants.AsyncAssistants(
                            client
                        ).update(
                            assistant_id=result.action_data.agent_id,
                            file_ids=file_ids,
                        )
                    )
                    print("AsyncAssistants.update()", pprint.pformat(assistant))
                    yield AGIEvent(
                        event_type=AGIEventType.NEW_FILE_ADDED,
                        event_data=AGIEventNewFileAdded(
                            agent_id=result.action_data.agent_id,
                            file_id=file.id,
                        ),
                    )
                elif result.action_type == AGIActionType.NEW_THREAD:
                    thread = await client.beta.threads.create()
                    yield AGIEvent(
                        event_type=AGIEventType.NEW_THREAD_CREATED,
                        event_data=AGIEventNewThreadCreated(
                            agent_id=result.action_data.agent_id,
                            thread_id=thread.id,
                        ),
                    )
                elif result.action_type == AGIActionType.RUN_THREAD:
                    run = await client.beta.threads.runs.create(
                        assistant_id=result.action_data.agent_id,
                        thread_id=result.action_data.thread_id,
                    )
                    yield AGIEvent(
                        event_type=AGIEventType.NEW_THREAD_RUN_CREATED,
                        event_data=AGIEventNewThreadRunCreated(
                            agent_id=result.action_data.agent_id,
                            thread_id=result.action_data.thread_id,
                            run_id=run.id,
                            run_status=run.status,
                        ),
                    )
                    work[
                        tg.create_task(
                            client.beta.threads.runs.retrieve(
                                thread_id=run.thread_id, run_id=run.id
                            )
                        )
                    ] = (
                        f"thread.runs.{run.id}",
                        (result, run),
                    )
                elif result.action_type == AGIActionType.ADD_MESSAGE:
                    message = await client.beta.threads.messages.create(
                        thread_id=result.action_data.thread_id,
                        role=result.action_data.message_role,
                        content=result.action_data.message_content,
                    )
                    yield AGIEvent(
                        event_type=AGIEventType.THREAD_MESSAGE_ADDED,
                        event_data=AGIEventThreadMessageAdded(
                            agent_id=result.action_data.agent_id,
                            thread_id=result.action_data.thread_id,
                            message_id=message.id,
                            message_role=result.action_data.message_role,
                            message_content=result.action_data.message_content,
                        ),
                    )
            elif work_name.startswith("thread.runs."):
                action_new_thread_run, _old_run = work_ctx
                if result.status == "completed":
                    yield AGIEvent(
                        event_type=AGIEventType.THREAD_RUN_COMPLETE,
                        event_data=AGIEventThreadRunComplete(
                            agent_id=action_new_thread_run.action_data.agent_id,
                            thread_id=result.thread_id,
                            run_id=result.id,
                            run_status=result.status,
                        ),
                    )
                    # TODO Send this similar to seed back to a feedback queue to
                    # process as an action for get thread messages
                    thread_messages = client.beta.threads.messages.list(
                        thread_id=result.thread_id,
                    )
                    thread_messages_iter = thread_messages.__aiter__()
                    work[
                        tg.create_task(
                            ignore_stopasynciteration(
                                thread_messages_iter.__anext__()
                            )
                        )
                    ] = (
                        f"thread.messages.{result.thread_id}",
                        (action_new_thread_run, thread_messages_iter),
                    )
                elif result.status in ("queued", "in_progress"):
                    yield AGIEvent(
                        event_type=AGIEventType.THREAD_RUN_IN_PROGRESS,
                        event_data=AGIEventThreadRunInProgress(
                            agent_id=action_new_thread_run.action_data.agent_id,
                            thread_id=result.thread_id,
                            run_id=result.id,
                            run_status=result.status,
                        ),
                    )
                    work[
                        tg.create_task(
                            asyncio_sleep_for_then_coro(
                                10,
                                client.beta.threads.runs.retrieve(
                                    thread_id=result.thread_id, run_id=result.id
                                ),
                            )
                        )
                    ] = (
                        f"thread.runs.{run.id}",
                        (action_new_thread_run, result),
                    )
                else:
                    yield AGIEvent(
                        event_type=AGIEventType.THREAD_RUN_EVENT_WITH_UNKNOWN_STATUS,
                        event_data=AGIEventThreadRunEventWithUnknwonStatus(
                            agent_id=action_new_thread_run.action_data.agent_id,
                            thread_id=result.thread_id,
                            run_id=result.id,
                            status=result.status,
                        ),
                    )
            elif work_name.startswith("thread.messages."):
                action_new_thread_run, thread_messages_iter = work_ctx
                _, _, thread_id = work_name.split(".", maxsplit=3)
                # The zeroith index is the most recent response
                """
                work[
                    tg.create_task(ignore_stopasynciteration(thread_messages_iter.__anext__()))
                ] = (work_name, work_ctx)
                """
                for content in result.content:
                    if content.type == "text":
                        yield AGIEvent(
                            event_type=AGIEventType.NEW_THREAD_MESSAGE,
                            event_data=AGIEventNewThreadMessage(
                                agent_id=action_new_thread_run.action_data.agent_id,
                                thread_id=result.thread_id,
                                message_role=result.role,
                                message_content_type=content.type,
                                message_content=content.text.value,
                            ),
                        )
        except:
            traceback.print_exc()
            yield AGIEvent(
                event_type=AGIEventType.ERROR,
                event_data=traceback.format_exc(),
            )

    yield AGIEvent(
        event_type=AGIEventType.END_EVENTS,
        event_data=None,
    )


class _STDIN_CLOSED:
    pass


STDIN_CLOSED = _STDIN_CLOSED()


def pdb_action_stream_get_user_input(user_name: str):
    user_input = ""
    sys_stdin_iter = sys.stdin.__iter__()
    try:
        while not user_input:
            print(f"{user_name}: ", end="\r")
            user_input = sys_stdin_iter.__next__().rstrip()
    except (KeyboardInterrupt, StopIteration):
        return STDIN_CLOSED
    return user_input


class _CURRENTLY_UNDEFINED:
    pass


CURRENTLY_UNDEFINED = _CURRENTLY_UNDEFINED()


class AsyncioLockedCurrentlyDict(collections.UserDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.currently = CURRENTLY_UNDEFINED
        self.lock = asyncio.Lock()
        self.currently_exists = asyncio.Event()

    def __setitem__(self, name, value):
        super().__setitem__(name, value)
        self.currently = value
        self.currently_exists.set()
        print("currently", value)

    async def __aenter__(self):
        await self.lock.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.lock.__aexit__(exc_type, exc_value, traceback)


async def pdb_action_stream(tg, user_name, agents, threads):
    while True:
        yield await asyncio.to_thread(
            pdb_action_stream_get_user_input, user_name
        )


async def main(
    user_name: str,
    agi_name: str,
    kvstore_service_name: str,
    *,
    kvstore: KVStore = None,
    action_stream: AGIActionStream = None,
    openai_api_key: str = None,
    openai_base_url: Optional[str] = None,
):
    if not kvstore:
        kvstore = KVStoreKeyring({"service_name": kvstore_service_name})

    kvstore_key_agent_id = f"agents.{agi_name}.id"
    action_stream_seed = [
        AGIAction(
            action_type=AGIActionType.NEW_AGENT,
            action_data=AGIActionNewAgent(
                agent_id=await kvstore.get(kvstore_key_agent_id, None),
                agent_name=agi_name,
                agent_instructions=pathlib.Path(__file__)
                .parent.joinpath("openai_assistant_instructions.md")
                .read_text(),
            ),
        ),
    ]

    agents = AsyncioLockedCurrentlyDict()
    threads = AsyncioLockedCurrentlyDict()

    async with kvstore, asyncio.TaskGroup() as tg:
        if not action_stream:
            unvalidated_user_input_action_stream = pdb_action_stream(
                tg,
                user_name,
                agents,
                threads,
            )

        user_input_action_stream_queue = asyncio.Queue()

        async def user_input_action_stream_queue_iterator(queue):
            # TODO Stop condition/asyncio.Event
            while True:
                yield await queue.get()

        action_stream = user_input_action_stream_queue_iterator(
            user_input_action_stream_queue,
        )

        for action in action_stream_seed:
            await user_input_action_stream_queue.put(action)

        if openai_api_key:
            agent_events = agent_openai(
                tg,
                agi_name,
                kvstore,
                action_stream,
                openai_api_key,
                openai_base_url=openai_base_url,
            )
        else:
            raise Exception(
                "No API keys or implementations of assistants given"
            )

        waiting = []

        unvalidated_user_input_action_stream_iter = (
            unvalidated_user_input_action_stream.__aiter__()
        )
        agent_events_iter = agent_events.__aiter__()
        work = {
            tg.create_task(
                ignore_stopasynciteration(
                    unvalidated_user_input_action_stream_iter.__anext__()
                )
            ): (
                "user.unvalidated.input_action_stream",
                unvalidated_user_input_action_stream_iter,
            ),
            tg.create_task(
                ignore_stopasynciteration(agent_events_iter.__anext__())
            ): (
                "agent.events",
                agent_events_iter,
            ),
        }
        async for (work_name, work_ctx), result in concurrently(work):
            if result is STOP_ASYNC_ITERATION:
                continue
            if work_name == "agent.events":
                work[
                    tg.create_task(
                        ignore_stopasynciteration(work_ctx.__anext__())
                    )
                ] = (work_name, work_ctx)
                agent_event = result
                pprint.pprint(agent_event)
                print(f"{user_name}: ", end="\r")
                if agent_event.event_type in (
                    AGIEventType.NEW_AGENT_CREATED,
                    AGIEventType.EXISTING_AGENT_RETRIEVED,
                ):
                    await kvstore.set(
                        f"agents.{agent_event.event_data.agent_name}.id",
                        agent_event.event_data.agent_id,
                    )
                    async with agents:
                        agents[agent_event.event_data.agent_id] = AGIState(
                            state_type=AGIStateType.AGENT,
                            state_data=AGIStateAgent(
                                agent_name=agent_event.event_data.agent_name,
                                agent_id=agent_event.event_data.agent_id,
                            ),
                        )
                elif agent_event.event_type == AGIEventType.NEW_THREAD_CREATED:
                    async with threads:
                        threads[agent_event.event_data.thread_id] = AGIState(
                            state_type=AGIStateType.THREAD,
                            state_data=AGIStateThread(
                                agent_id=agent_event.event_data.agent_id,
                                thread_id=agent_event.event_data.thread_id,
                            ),
                        )
                    async with agents:
                        """
                        agents[
                            agent_event.event_data.agent_id
                        ].state_data.thread_ids.append(
                            agent_event.event_data.thread_id
                        )
                        """
                        print(agents[agent_event.event_data.agent_id])
                elif (
                    agent_event.event_type
                    == AGIEventType.NEW_THREAD_RUN_CREATED
                ):
                    async with threads:
                        thread_state = threads[agent_event.event_data.thread_id]
                        thread_state.most_recent_run_id = (
                            agent_event.event_data.run_id
                        )
                        thread_state.most_recent_run_status = (
                            agent_event.event_data.run_status
                        )
                        print(thread_state)
                elif (
                    agent_event.event_type
                    == AGIEventType.THREAD_RUN_IN_PROGRESS
                ):
                    async with threads:
                        threads[
                            agent_event.event_data.thread_id
                        ].state_data.most_recent_run_status = (
                            agent_event.event_data.run_status
                        )
                elif agent_event.event_type == AGIEventType.THREAD_RUN_COMPLETE:
                    async with threads:
                        threads[
                            agent_event.event_data.thread_id
                        ].state_data.most_recent_run_status = (
                            agent_event.event_data.run_status
                        )
                        print(threads[agent_event.event_data.thread_id])
                    async with agents:
                        print(agents[agent_event.event_data.agent_id])
                        """
                        agents[
                            agent_event.event_data.agent_id
                        ].state_data.thread_ids.remove(
                            agent_event.event_data.thread_id
                        )
                        print(agents[agent_event.event_data.agent_id])
                        """
                elif agent_event.event_type == AGIEventType.NEW_THREAD_MESSAGE:
                    async with agents:
                        agent_state = agents[agent_event.event_data.agent_id]
                    # TODO https://rich.readthedocs.io/en/stable/markdown.html
                    if agent_event.event_data.message_content_type == "text":
                        print(
                            f"{agent_state.state_data.agent_name}: {agent_event.event_data.message_content}"
                        )
                        print(f"{user_name}: ", end="\r")
                # Run any actions which have been waiting for an event
                still_waiting = []
                while waiting:
                    action_waiting_for_event, make_action = waiting.pop(0)
                    if action_waiting_for_event == agent_event.event_type:
                        await user_input_action_stream_queue.put(
                            await make_action()
                        )
                    else:
                        still_waiting.append(
                            (action_waiting_for_event, make_action)
                        )
                waiting.extend(still_waiting)
            elif work_name == "user.unvalidated.input_action_stream":
                work[
                    tg.create_task(
                        ignore_stopasynciteration(work_ctx.__anext__())
                    )
                ] = (work_name, work_ctx)
                user_input = result
                if pathlib.Path(user_input).is_file():
                    await user_input_action_stream_queue.put(
                        AGIAction(
                            action_type=AGIActionType.INGEST_FILE,
                            action_data=AGIActionIngestFile(
                                agent_id=agents.currently.state_data.agent_id,
                                file_path=user_input,
                            ),
                        ),
                    )
                    continue
                waiting.append(
                    (
                        AGIEventType.THREAD_MESSAGE_ADDED,
                        async_lambda(
                            lambda: AGIAction(
                                action_type=AGIActionType.RUN_THREAD,
                                action_data=AGIActionRunThread(
                                    agent_id=threads.currently.state_data.agent_id,
                                    thread_id=threads.currently.state_data.thread_id,
                                ),
                            )
                        ),
                    ),
                )
                # TODO Handle case where agent does not yet exist
                """
                async with agents:
                    active_agent_currently_undefined = (
                        agents.currently == CURRENTLY_UNDEFINED
                    )
                if active_agent_currently_undefined:
                    await tg.create_task(agents.currently_exists.wait())
                """
                async with threads:
                    active_thread_currently_undefined = (
                        threads.currently == CURRENTLY_UNDEFINED
                    )
                if active_thread_currently_undefined:
                    async with agents:
                        current_agent = agents.currently
                    if not isinstance(user_input, AGIAction):
                        waiting.append(
                            (
                                AGIEventType.NEW_THREAD_CREATED,
                                async_lambda(
                                    lambda: AGIAction(
                                        action_type=AGIActionType.ADD_MESSAGE,
                                        action_data=AGIActionAddMessage(
                                            agent_id=agents.currently.state_data.agent_id,
                                            thread_id=threads.currently.state_data.thread_id,
                                            message_role="user",
                                            message_content=user_input,
                                        ),
                                    )
                                ),
                            ),
                        )
                    await user_input_action_stream_queue.put(
                        AGIAction(
                            action_type=AGIActionType.NEW_THREAD,
                            action_data=AGIActionNewThread(
                                agent_id=current_agent.state_data.agent_id,
                            ),
                        ),
                    )
                else:
                    await user_input_action_stream_queue.put(
                        AGIAction(
                            action_type=AGIActionType.ADD_MESSAGE,
                            action_data=AGIActionAddMessage(
                                agent_id=agents.currently.state_data.agent_id,
                                thread_id=threads.currently.state_data.thread_id,
                                message_role="user",
                                message_content=user_input,
                            ),
                        ),
                    )


if __name__ == "__main__":
    # TODO Hook each thread to a terminal context with tmux
    parser = make_argparse_parser()

    args = parser.parse_args(sys.argv[1:])

    import httptest

    with httptest.Server(
        httptest.CachingProxyHandler.to(
            str(openai.AsyncClient(api_key="Alice").base_url),
            state_dir=str(
                pathlib.Path(__file__).parent.joinpath(".cache", "openai")
            ),
        )
    ) as cache_server:
        # args.openai_base_url = cache_server.url()
        asyncio.run(main(**vars(args)))
