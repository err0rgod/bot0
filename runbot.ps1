$ImageName = "zeroday_bot"

Write-Host "Checking if Docker image '$ImageName' exists..."
$imageExists = docker images -q $ImageName
if (-not $imageExists) {
    Write-Host "Docker image not found. Building it..."
    docker build -t $ImageName .
}

Write-Host "Starting the bot in Docker..."
$currentPath = (Get-Location).Path
docker run --rm `
    --name "${ImageName}_run" `
    --env-file .env `
    -v "${currentPath}/data:/app/data" `
    --cpus="1.0" `
    --memory="512m" `
    $ImageName
