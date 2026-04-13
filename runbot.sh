#!/bin/bash

IMAGE_NAME="zeroday_bot"

echo "Checking if Docker image '$IMAGE_NAME' exists..."
if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo "Docker image not found. Building it..."
    docker build -t "$IMAGE_NAME" .
fi

echo "Starting the bot in Docker..."
docker run --rm \
    --name "${IMAGE_NAME}_run" \
    --env-file .env \
    -v "$(pwd)/data:/app/data" \
    --cpus="1.0" \
    --memory="512m" \
    "$IMAGE_NAME"
