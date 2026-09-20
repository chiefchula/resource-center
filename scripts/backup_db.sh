#!/usr/bin/env bash
#
# Backup the SQLite database.
# Usage: ./scripts/backup_db.sh
#
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_FILE="${PROJECT_ROOT}/instance/rescue_center.db"
BACKUP_DIR="${PROJECT_ROOT}/backups"
KEEP_DAYS=30

if [ ! -f "${DB_FILE}" ]; then
    echo "❌ Database not found at ${DB_FILE}"
    exit 1
fi

mkdir -p "${BACKUP_DIR}"
STAMP="$(date +%Y-%m-%d_%H%M%S)"
TARGET="${BACKUP_DIR}/rescue_center_${STAMP}.db"

# Use SQLite's .backup command for a consistent snapshot
# (avoids copying a file mid-write)
if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "${DB_FILE}" ".backup '${TARGET}'"
else
    cp "${DB_FILE}" "${TARGET}"
fi

echo "✔ Backup created: ${TARGET}"
echo "   Size: $(du -h "${TARGET}" | cut -f1)"

# Prune backups older than KEEP_DAYS
find "${BACKUP_DIR}" -name 'rescue_center_*.db' -type f -mtime +${KEEP_DAYS} -delete
echo "✔ Pruned backups older than ${KEEP_DAYS} days"