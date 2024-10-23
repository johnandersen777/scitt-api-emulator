# export GITHUB_USER=pdxjohnny; ssh -t root@alice.chadig.com rm -f /tmp/$GITHUB_USER; ssh -tt -R /tmp/$GITHUB_USER:/tmp/local_socket -o StreamLocalBindUnlink=yes -o PermitLocalCommand=yes -o LocalCommand="setsid socat EXEC:${SHELL},stderr,pty UNIX-LISTEN:/tmp/local_socket,unlink-early &" root@alice.chadig.com python3.11 socket_pty_attach_4.py /tmp/agi.sock /tmp/$GITHUB_USER $GITHUB_USER
import argparse
import asyncio
import os
import socket
import sys
import tty
import termios
import signal
import aiohttp
from aiohttp import UnixConnector
import fcntl
import json
from pydantic import BaseModel


def set_nonblocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)


def tee_data(input_fd, output_fd_client, output_fd_stdout, control_state):
    output_fd_client_dup = os.dup(output_fd_client)
    output_fd_stdout_dup = os.dup(output_fd_stdout)

    try:
        while True:
            bytes_in = os.splice(input_fd, None, output_fd_client_dup, None, 65536)
            if bytes_in == 0:
                break

            if control_state["splice_to_stdout"]:
                os.splice(
                    output_fd_client_dup, None, output_fd_stdout_dup, None, bytes_in
                )

    except BlockingIOError:
        pass
    except OSError as e:
        print(f"Splice error: {e}")
    finally:
        os.close(output_fd_client_dup)
        os.close(output_fd_stdout_dup)


async def handle_splice_sockets(client_pty_as_sock_fd, control_sock_fd, control_state):
    loop = asyncio.get_event_loop()

    set_nonblocking(sys.stdin.fileno())
    set_nonblocking(sys.stdout.fileno())
    set_nonblocking(client_pty_as_sock_fd)

    loop.add_reader(
        sys.stdin.fileno(),
        tee_data,
        sys.stdin.fileno(),
        client_pty_as_sock_fd,
        sys.stdout.fileno(),
        control_state,
    )
    loop.add_reader(
        client_pty_as_sock_fd,
        tee_data,
        client_pty_as_sock_fd,
        sys.stdout.fileno(),
        sys.stdout.fileno(),
        control_state,
    )

    while True:
        await asyncio.sleep(0.01)


async def send_ctrl_c(client_pty_as_sock):
    client_pty_as_sock.send(b"\x03")


def setup_sigint_handler(client_pty_as_sock):
    signal.signal(
        signal.SIGINT,
        lambda sig, frame: asyncio.create_task(send_ctrl_c(client_pty_as_sock)),
    )


async def get_socket_paths(session, user):
    async with session.get(f"http://localhost/{user}/connect/pty") as response:
        if response.status == 200:
            json_data = await response.json()
            return {
                "socket_pty_stdio": json_data.get("socket_pty_stdio"),
                "socket_control_pty_stdio": json_data.get("socket_control_pty_stdio"),
            }
        else:
            raise RuntimeError(f"Failed to get socket paths for user {user}: {await response.text()}")


async def handle_sse_control(session, user, control_socket_path, control_state):
    async with session.get(f"http://localhost/{user}/connect/pty/control-stream") as response:
        async for line in response.content:
            if isinstance(line, bytes):
                message = line.decode("utf-8").strip()
                if message.startswith("data: "):
                    json_message = message[6:].strip()
                    try:
                        data = json.loads(json_message)
                        control_state["splice_to_stdout"] = data["splice_to_stdout"]
                    except json.JSONDecodeError as e:
                        print(f"Failed to decode message: {json_message} with error: {e}")


class ConnectionArgs(BaseModel):
    server_agi_socket_path: str
    client_pty_socket_path: str
    user: str


async def handle_connect_pty(args: ConnectionArgs):
    async with aiohttp.ClientSession(
        connector=aiohttp.UnixConnector(path=args.server_agi_socket_path)
    ) as session:
        socket_paths = await get_socket_paths(session, args.user)
        socket_pty_stdio = socket_paths.get("socket_pty_stdio")
        socket_control_pty_stdio = socket_paths.get("socket_control_pty_stdio")

        if not socket_pty_stdio or not socket_control_pty_stdio:
            raise RuntimeError(f"Required socket paths not found in response.")

        client_pty_as_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_pty_as_sock.connect(args.client_pty_socket_path)

        control_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        control_sock.connect(socket_pty_stdio)

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)

            setup_sigint_handler(client_pty_as_sock)

            control_state = {"splice_to_stdout": True}

            asyncio.create_task(
                handle_sse_control(
                    session, args.user, socket_control_pty_stdio, control_state
                )
            )
            await handle_splice_sockets(
                client_pty_as_sock.fileno(), control_sock.fileno(), control_state
            )

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        client_pty_as_sock.close()
        control_sock.close()


async def main():
    parser = argparse.ArgumentParser(
        description="Connect stdin and sockets via splice."
    )
    parser.add_argument(
        "server_agi_socket_path",
        type=str,
        help="Path to the server UNIX socket.",
        default="/host/agi.sock",
    )
    parser.add_argument(
        "client_pty_socket_path", type=str, help="Path to the client Unix socket."
    )
    parser.add_argument("user", type=str, help="Username to connect to the service.")
    parsed_args = parser.parse_args()

    args = ConnectionArgs(
        server_agi_socket_path=parsed_args.server_agi_socket_path,
        client_pty_socket_path=parsed_args.client_pty_socket_path,
        user=parsed_args.user,
    )

    await handle_connect_pty(args)


if __name__ == "__main__":
    asyncio.run(main())
