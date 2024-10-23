(
set -x \
&& if [ ! -d ~/agi ]; then git clone https://gist.github.com/pdxjohnny/2bb4bb6d7a6abaa07cebc7c04d1cafa5 ~/agi/; fi \
&& cd ~/agi/ \
&& git pull \
&& docker build -t alice-server -f alice.Dockerfile . \
&& docker kill alice-server \
&& docker rm alice-server \
&& docker run --detach --restart=always --name=alice-server -p 2222:22 -e OPENAI_API_KEY="sk-maryisgod" alice-server \
&& docker logs -f alice-server
)
