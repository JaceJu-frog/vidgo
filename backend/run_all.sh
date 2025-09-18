#!/usr/bin/env bash
set -euo pipefail

mkdir -p ./logs

export PORT="${PORT:-8000}"
export VIDGO_URL="${VIDGO_URL:-https://vidgo.cemp.top}"

# 你的项目用的是 vid_go.settings -> 对应的 WSGI 入口如下
APP_MODULE="vid_go.wsgi:application"
LOG="./logs/gunicorn_$(date +%Y%m%d_%H%M%S).log"

echo "Using $(python -V) at $(which python)"

# 如被占用则报错并给出提示
if lsof -t -i tcp:"$PORT" >/dev/null 2>&1; then
  echo "ERROR: Port $PORT in use by PID(s): $(lsof -t -i tcp:$PORT | xargs)"
  echo "Hint: fuser -k ${PORT}/tcp   或   pkill -f 'manage.py runserver.*${PORT}'"
  exit 1
fi

# 若当前不在 manage.py 所在目录，可加 --chdir "$(dirname "$0")"
nohup python -m gunicorn "$APP_MODULE" \
  --bind "0.0.0.0:${PORT}" \
  --workers "$(( 2*$(nproc) + 1 ))" \
  --access-logfile - --log-level info \
  >> "$LOG" 2>&1 & PID=$!

echo "PID=$PID"
echo "Local:   http://localhost:${PORT}/"
hostname -I | xargs -n1 -I{} echo "Network: http://{}:${PORT}/"
echo "Log:     $(pwd)/$LOG"
echo "VIDGO_URL=$VIDGO_URL"

# 想现场看日志就保留这行；不想阻塞就注释掉
tail -n 50 -f "$LOG"
