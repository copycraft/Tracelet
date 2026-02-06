# init_db.ps1

# --- Config ---
$containerName = "tracelet-db"
$dbUser = "tracelet_user"
$dbPassword = "password"
$dbName = "tracelet_db"
$hostPort = 5432

# --- Check Docker ---
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker not found! Please install Docker Desktop first."
    exit
}

# --- Check if container is running ---
$container = docker ps -a --filter "name=$containerName" --format "{{.Names}}"

if (-not $container) {
    Write-Output "PostgreSQL container not found. Creating a new one..."
    docker run --name $containerName `
        -e POSTGRES_USER=$dbUser `
        -e POSTGRES_PASSWORD=$dbPassword `
        -e POSTGRES_DB=$dbName `
        -p $hostPort:5432 `
        -d postgres
} elseif (-not (docker ps --filter "name=$containerName" --format "{{.Names}}")) {
    Write-Output "Starting existing PostgreSQL container..."
    docker start $containerName
} else {
    Write-Output "PostgreSQL container is already running."
}

# --- Wait for PostgreSQL to be ready ---
Write-Output "Waiting for PostgreSQL to be ready..."
do {
    Start-Sleep -Seconds 2
    $ready = docker exec $containerName pg_isready -U $dbUser -d $dbName -h localhost
} until ($ready -like "*accepting connections*")

Write-Output "PostgreSQL is ready!"

# --- Create tables if they don't exist ---
# Example SQL for 'entities' table. Add more tables here as needed.
$sql = @"
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    external_id VARCHAR(50),
    extra_data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
"@

# Execute SQL inside the container
docker exec -i $containerName psql -U $dbUser -d $dbName -c "$sql"

Write-Output "Database tables ensured!"
Write-Output "Connect using: Host=localhost, Port=$hostPort, User=$dbUser, Password=$dbPassword, DB=$dbName"
