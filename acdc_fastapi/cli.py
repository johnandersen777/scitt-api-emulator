import argparse
import uvicorn
from acdc_fastapi.app import app

def run_server(addr: str, port: int):
    uvicorn.run(app, host=addr, port=port)

def main():
    parser = argparse.ArgumentParser(description="Run Alice or Bob's FastAPI server")
    parser.add_argument('--port', type=int, default=8000, help='Port to bind the server')
    parser.add_argument('--addr', type=str, default="127.0.0.1", help='Which addr to bind to. Default: 127.0.0.1')
    args = parser.parse_args()
    run_server(args.addr, args.port)

if __name__ == "__main__":
    main()
