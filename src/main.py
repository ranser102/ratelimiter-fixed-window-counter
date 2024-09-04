"""This module creating api endpoints for Rate Limiter."""

import sys
from fastapi import FastAPI, HTTPException
import uvicorn

from ratelimit_memcached import rate_limit, get_balance

app = FastAPI()

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to RateLimiter with Memcached!"}

@app.get("/ratelimit")
async def check_rate_limit(key: str, interval: int=60, max_limit: int=1):
    """ Check rate limit for a key in a given interval."""  
    try:
        if rate_limit(str(key), int(interval), int(max_limit)):
            raise HTTPException(status_code=429, detail={"Block": True, "key": key})
        return {"Block": False, "key": key}
    except HTTPException as httpexcep:
        raise httpexcep
    except Exception as genericerror:
        # Log the error
        print(f"Unexpected error: {genericerror}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Internal server error") from genericerror

@app.get("/checkbalance")
async def check_balance(key: str):
    """Check balance for a key."""
    try:
        balance = get_balance(key)
        return {"key": key, "balance": balance}
    except Exception as genericerror:
        # Log the error
        print(f"Unexpected error: {genericerror}", file=sys.stderr)
        raise HTTPException(status_code=500, detail="Internal server error") from genericerror



def main():
    """Main function to run the FastAPI app."""
    try:
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as genericerror:
        print(f"Unexpected error: {genericerror}", file=sys.stderr)
        raise SystemExit(1) from genericerror
# uvicorn app.main:app --reload

if __name__ == "__main__":
    main()
