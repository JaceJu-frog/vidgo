mkdir -p ~/logs && \
PORT=8080 && \
VIDGO_URL=https://vidgo.cemp.top nohup "$(which python)" manage.py runserver 0.0.0.0:$PORT >> ~/logs/vidgo.run.log 2>&1 & PID=$! && \
echo "PID=$PID" && \
echo "Local:   http://localhost:$PORT/" && \
hostname -I | xargs -n1 | while read ip; do echo "Network: http://$ip:$PORT/"; done && \
echo "Log:     $HOME/logs/vidgo.run.log" && \
echo "VIDGO_URL=$VIDGO_URL"
