poetry export -o requirements.txt --without-hashes

docker compose build
docker compose up
