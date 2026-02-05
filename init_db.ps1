# Save as init_db.ps1

# Check if Docker is installed
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found! Please install Docker Desktop first."
    exit
}

# Run PostgreSQL container
docker run --name tracelet-db `
    -e POSTGRES_USER=tracelet_user `
    -e POSTGRES_PASSWORD=password `
    -e POSTGRES_DB=tracelet_db `
    -p 5432:5432 `
    -d postgres

Write-Output "PostgreSQL container started!"
Write-Output "Connect to it using:"
Write-Output "Host: localhost, Port: 5432, User: tracelet_user, Password: password, DB: tracelet_db"
