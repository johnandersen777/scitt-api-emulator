# ACDC FastAPI

This project sets up two FastAPI servers, Alice and Bob, running on separate ports using Docker containers.

## Setup Instructions

1. **Create virtual environment**:
   ```bash
   ./setup.sh
   ```

2. **Run the servers**:
   You can run a FastAPI server using the CLI:
   ```bash
   start-server --port 8000
   ```

3. **Run tests**:
   To run the Docker test case:
   ```bash
   pytest tests/test_docker.py
   ```
