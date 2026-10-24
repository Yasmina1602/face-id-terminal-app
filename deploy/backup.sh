#!/bin/bash
# ========================================================
# PostgreSQL Zaxira Nusxalash Skripti (Har kecha cron orqali)
# ========================================================
set -e

BACKUP_DIR="/var/backups/davomat"
mkdir -p "$BACKUP_DIR"

DATE_STR=$(date +%F_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/attand_${DATE_STR}.sql.gz"

echo "[$(date)] Zaxira olish boshlandi: $BACKUP_FILE"

# Agar Docker konteynerda bo'lsa:
if docker ps | grep -q "davomat-db"; then
    docker exec davomat-db pg_dump -U root root | gzip > "$BACKUP_FILE"
else
    # Lokal PostgreSQL bo'lsa:
    pg_dump -h 127.0.0.1 -p 5432 -U root root | gzip > "$BACKUP_FILE"
fi

echo "[$(date)] Zaxira muvaffaqiyatli saqlandi: $(ls -lh "$BACKUP_FILE" | awk '{print $5}')"

# 14 kundan eski zaxira nusxalarini tozalash
find "$BACKUP_DIR" -name "attand_*.sql.gz" -mtime +14 -delete
echo "[$(date)] 14 kundan eski zaxiralar tozalandi."
