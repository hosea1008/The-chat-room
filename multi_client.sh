#!/usr/bin/zsh
python server.py &
cd /home/hsli/workshop/go_projects/udt_server/ || exit
go run udt_server.go &
cd /home/hsli/workshop/The-chat-room/ || exit
sleep 2s
echo "Server started..."
 for user in {A..C} ; do
       python client.py "127.0.0.1" $user &
       echo "Client" $user "started..."
       sleep 0.5s
 done
