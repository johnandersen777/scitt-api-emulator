import argparse
import uvicorn
from acdc_fastapi.app import app_alice, app_bob

def run_server(port: int, server: str):
    if server == 'alice':
        print(f"Starting Alice's server on port {port}...")
        uvicorn.run(app_alice, host="0.0.0.0", port=port)
    elif server == 'bob':
        print(f"Starting Bob's server on port {port}...")
        uvicorn.run(app_bob, host="0.0.0.0", port=port)

def main():
    parser = argparse.ArgumentParser(description="Run Alice or Bob's FastAPI server")
    parser.add_argument('--port', type=int, default=8000, help='Port to bind the server')
    parser.add_argument('--server', type=str, choices=['alice', 'bob'], required=True, help='Which server to start: alice or bob')
    args = parser.parse_args()
    run_server(args.port, args.server)

if __name__ == "__main__":
    main()
