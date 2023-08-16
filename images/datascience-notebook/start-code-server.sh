#!/bin/bash

CODE_SERVER_PORT=${CODE_SERVER_PORT:-"8889"}

code-server --log debug --bind-addr 0.0.0.0:${CODE_SERVER_PORT} > "/tmp/code-server.log" 2>&1 &
