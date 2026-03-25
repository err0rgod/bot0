#!/bin/bash

echo "Fetching latest changes from origin..."
git fetch --all

# Get the current branch name
BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "Resetting current branch ($BRANCH) to upstream..."
git reset --hard origin/$BRANCH

echo "Update complete."
