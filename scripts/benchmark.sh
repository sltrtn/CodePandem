#!/usr/bin/env bash
set -euo pipefail

# CodePandem Performance Benchmark
# Usage: ./scripts/benchmark.sh [endpoint] [duration] [connections] [threads]

ENDPOINT="${1:-/health}"
DURATION="${2:-10s}"
CONNECTIONS="${3:-100}"
THREADS="${4:-4}"

HOST="${BENCH_HOST:-localhost}"
PORT="${BENCH_PORT:-8080}"
URL="http://${HOST}:${PORT}${ENDPOINT}"

echo "============================================"
echo "  CodePandem Benchmark"
echo "============================================"
echo "  Target:    ${URL}"
echo "  Duration:  ${DURATION}"
echo "  Conns:     ${CONNECTIONS}"
echo "  Threads:   ${THREADS}"
echo "============================================"
echo ""

# Check wrk is installed
if ! command -v wrk &> /dev/null; then
    echo "wrk not found. Install it:"
    echo "  sudo apt install wrk"
    echo "  # or on macOS: brew install wrk"
    exit 1
fi

echo "--- Baseline: No caching ---"
wrk -t${THREADS} -c${CONNECTIONS} -d${DURATION} --latency "${URL}"

echo ""
echo "--- Done ---"
echo ""
echo "Compare with Redis-cached endpoint:"
echo "  wrk -t${THREADS} -c${CONNECTIONS} -d${DURATION} --latency http://${HOST}:${PORT}/api/leaderboard"
