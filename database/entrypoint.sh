#!/bin/bash
set -e

echo "Starting SQL Server..."
/opt/mssql/bin/sqlservr &

pid="$!"

echo "Waiting for SQL Server to be ready..."

# wait until SQL is ready
for i in {1..60}; do
  /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -Q "SELECT 1" -C >/dev/null 2>&1 && break
  echo "  -> still starting... ($i/60)"
  sleep 2
done

echo "SQL Server is up. Restoring LoanDataDB..."

# Drop existing DB
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -Q "
IF DB_ID('LoanDataDB') IS NOT NULL
BEGIN
    ALTER DATABASE LoanDataDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE LoanDataDB;
END
" -C

# Restore DB
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$SA_PASSWORD" -Q "
RESTORE DATABASE LoanDataDB
FROM DISK = '/var/opt/mssql/backup/LoanDataDB.bak'
WITH REPLACE,
MOVE 'LoanDataDB' TO '/var/opt/mssql/data/LoanDataDB.mdf',
MOVE 'LoanDataDB_log' TO '/var/opt/mssql/data/LoanDataDB_log.ldf';
" -C

echo "Restore LoanDataDB completed."

wait "$pid"
