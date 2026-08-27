#!/usr/bin/env bash
set -euo pipefail

# Run benchmarks against multiple endpoints
# Usage: ./scripts/benchmark-all.sh

HOST="${BENCH_HOST:-localhost}"
PORT="${BENCH_PORT:-8080}"
DURATION="10s"
CONNECTIONS="100"
THREADS="4"

echo "============================================"
echo "  CodePandem Full Benchmark Suite"
echo "============================================"
echo ""

# 1. Health endpoint (no DB, no cache)
echo "[1/4] Health endpoint (baseline - no DB)"
echo "-------------------------------------------"
wrk -t${THREADS} -c${CONNECTIONS} -d${DURATION} --latency "http://${HOST}:${PORT}/health"
echo ""

# 2. Static JSON endpoint
echo "[2/4] Leaderboard (DB query, no cache)"
echo "-------------------------------------------"
wrk -t${THREADS} -c${CONNECTIONS} -d${DURATION} --latency "http://${HOST}:${PORT}/api/leaderboard"
echo ""

# 3. Leaderboard with Redis cache (once you implement caching)
echo "[3/4] Leaderboard (with Redis cache)"
echo "-------------------------------------------"
wrk -t${THREADS} -c${CONNECTIONS} -d${DURATION} --latency "http://${HOST}:${PORT}/api/leaderboard?cached=1" || echo "(not implemented yet)"
echo ""

# 4. Auth endpoint (write path)
echo "[4/4] Register endpoint (write path)"
echo "-------------------------------------------"
# This will fail with duplicate user, but measures latency under load
wrk -t${THREADS} -c${CONNECTIONS} -d${DURATION} --latency \
    -s <(echo '
        wrk.method = "POST"
        wrk.headers["Content-Type"] = "application/json"
        function request()
            return wrk.format(nil, "/api/auth/register", nil,
                string.format("{\"username\":\"bench_%d\",\"password\":\"test1234\"}", math.random(1, 100000)))
        end
    ') "http://${HOST}:${PORT}" || echo "(expected: 4xx errors under concurrent writes)"
echo ""

echo "============================================"
echo "  Benchmark suite complete"
echo "============================================"
