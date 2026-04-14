#!/bin/bash
cd /home/err0rgod/bot0
pwd
IMAGE_NAME="zeroday_bot"

echo "Checking if Docker image '$IMAGE_NAME' exists..."
if ! /usr/bin/docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "Docker image not found. Building it..."
    /usr/bin/docker build -t "$IMAGE_NAME" .
fi

echo "Starting the bot in Docker..."
/usr/bin/docker run --rm \
    --name "${IMAGE_NAME}_run" \
    --env-file /home/err0rgod/bot0/.env \
    -v "/home/err0rgod/bot0/data:/app/data" \
    --cpus="1.0" \
    --memory="2048m" \
    "$IMAGE_NAME"
