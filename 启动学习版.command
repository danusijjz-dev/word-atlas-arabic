#!/bin/zsh
set -e

cd "$(dirname "$0")"
PORT=5188
URL="http://127.0.0.1:${PORT}/#/atlas"

if ! curl -fsS --max-time 1 "$URL" >/dev/null 2>&1; then
  /usr/bin/python3 "$PWD/serve.py" &
  SERVER_PID=$!
  trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM
fi

sleep 1
open "$URL"
echo
echo "词光·英阿双语学习版已启动："
echo "$URL"
echo
echo "保持此窗口打开即可使用。关闭窗口会停止本地网站。"

if [[ -n "${SERVER_PID:-}" ]]; then
  wait "$SERVER_PID"
else
  read -r "?按回车键退出…"
fi
