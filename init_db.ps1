# init_db.ps1
# Simple DB init for Tracelet (no Alembic)

# --- Config ---
$containerName = 'tracelet-db'
$dbUser = 'tracelet_user'
$dbPassword = 'password'
$dbName = 'tracelet_db'
$hostPort = 5432

# --- Check Docker ---
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'Docker not found! Install Docker Desktop first.'
    exit 1
}

# --- Ensure container exists ---
$exists = docker ps -a --filter "name=$containerName" --format "{{.Names}}"
$running = docker ps --filter "name=$containerName" --format "{{.Names}}"

if (-not $exists) {
    Write-Output 'Creating PostgreSQL container...'
    docker run --name $containerName -e POSTGRES_USER=$dbUser -e POSTGRES_PASSWORD=$dbPassword -e POSTGRES_DB=$dbName -p $hostPort:5432 -d postgres
} elseif (-not $running) {
    Write-Output 'Starting existing container...'
    docker start $containerName | Out-Null
} else {
    Write-Output 'PostgreSQL container already running.'
}

# --- Wait for Postgres ---
Write-Output 'Waiting for PostgreSQL to be ready...'
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Seconds 2
    $ready = docker exec $containerName pg_isready -U $dbUser -d $dbName -h localhost
    if ($ready -match 'accepting connections') { break }
}
if ($ready -notmatch 'accepting connections') {
    Write-Error 'Postgres did not become ready in time.'
    exit 1
}

Write-Output 'PostgreSQL ready!'

# --- Create tables ---
Write-Output 'Creating required tables if missing...'

$tempFile = Join-Path $env:TEMP 'tracelet_tables.sql'

@'
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS entity_links (
    id SERIAL PRIMARY KEY,
    from_entity INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    to_entity INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) PRIMARY KEY
);
'@ | Out-File -FilePath $tempFile -Encoding UTF8

# Pipe SQL into psql inside container
Get-Content -Path $tempFile -Raw | docker exec -i $containerName psql -U $dbUser -d $dbName -f -

# Cleanup
Remove-Item -Path $tempFile -ErrorAction SilentlyContinue

# --- Show tables ---
docker exec -i $containerName psql -U $dbUser -d $dbName -c '\dt'

Write-Output ''
Write-Output '==================================='
Write-Output 'Database setup complete!'
Write-Output 'Tables created: alembic_version, entities, events, entity_links'
Write-Output '==================================='
