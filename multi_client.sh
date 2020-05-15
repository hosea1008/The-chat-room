#!/usr/bin/zsh
python server.py &
go run /home/hsli/workshop/go_projects/udt_server/udt_server.go &
sleep 3s
echo "Server started..."
for user in {A..C} ; do
  python client.py "127.0.0.1" $user &
  echo "Client" $user "started..."
  sleep 1s
done