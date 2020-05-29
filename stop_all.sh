#!/usr/bin/zsh
kill $(ps -aux | grep -E "python\s+[a-z]+\.py" | awk '{print $2}')
kill $(ps -aux | grep -E "udt_server" | awk '{print $2}')