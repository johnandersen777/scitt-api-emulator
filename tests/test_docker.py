import docker
import pathlib
import time

def poll_file_for_log(file, timeout=5):
    start_time = time.time()
    while time.time() - start_time < timeout:
        if pathlib.Path(file).exists():
            return True
        time.sleep(0.01)
    return False

def test_docker_containers():
    client = docker.from_env()

    alice_log = "alice.log"
    bob_log = "bob.log"

    # Start Alice container
    alice = client.containers.run(
        "acdc_fastapi", detach=True, ports={'8000/tcp': 8000}, name="alice", command="start-server --server alice --port 8000"
    )
    assert poll_file_for_log(alice_log)

    # Start Bob container
    bob = client.containers.run(
        "acdc_fastapi", detach=True, ports={'8001/tcp': 8001}, name="bob", command="start-server --server bob --port 8001"
    )
    assert poll_file_for_log(bob_log)

    # Cleanup
    alice.stop()
    bob.stop()
    alice.remove()
    bob.remove()
