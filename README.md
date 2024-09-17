# ACDC FastAPI

This project sets up two FastAPI servers, Alice and Bob, running on separate ports using Docker containers. It verifies ACDC messages between Alice and Bob.

## Setup Instructions

1. **Create virtual environment**:
   ```bash
   ./setup.sh
   ```

2. **Run Alice or Bob servers**:
   You can run Alice or Bob's FastAPI server using the CLI:
   ```bash
   start-server --server alice --port 8000
   start-server --server bob --port 8001
   ```

3. **Run tests**:
   To run the Docker test case:
   ```bash
   pytest tests/test_docker.py
   ```
