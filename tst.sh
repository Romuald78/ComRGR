#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Bad nb args !"
    exit 1
fi

for i in $(seq "$1"); do
    python3 2>"log_client_$i.log" "main.py" "client" &
    pid="$!"
    echo "Launched client with PID = $pid..."
done 

# echo "Starting server..."
# python3 2>"log_server.log" "main.py" "server" "$1"


