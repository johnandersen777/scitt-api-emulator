import argparse
import uvicorn
from acdc_fastapi.app import app

def run_server(port: int):
    print(f"Starting server on port {port}...")
    uvicorn.run("acdc_fastapi.app:app", host="0.0.0.0", port=port)

def main():
    parser = argparse.ArgumentParser(description="Run FastAPI server")
    parser.add_argument('--port', type=int, default=8000, help='Port to bind the server')
    args = parser.parse_args()
    run_server(args.port)

if __name__ == "__main__":
    main()
