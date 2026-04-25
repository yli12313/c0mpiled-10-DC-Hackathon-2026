#!/bin/bash
export GROQ_API_KEY="${GROQ_API_KEY:?Set GROQ_API_KEY first}"
export PGPASSWORD=postgres

cd "$(dirname "$0")"
/Users/yli/Library/Python/3.9/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
