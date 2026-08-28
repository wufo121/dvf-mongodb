#!/usr/bin/env bash
# Restauration de la base DVF (livrable 6).
#
# Usage : ./scripts/restore.sh backups/dvf_20250828_101500
set -euo pipefail

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "${MONGODB_URI:-}" ]; then
  echo "MONGODB_URI absent. Copiez .env.example en .env." >&2
  exit 1
fi

if [ $# -lt 1 ]; then
  echo "Usage : $0 <dossier_de_sauvegarde>" >&2
  exit 1
fi

SRC="$1/${DB_NAME:-dvf}"
if [ ! -d "$SRC" ]; then
  echo "Dossier introuvable : $SRC" >&2
  exit 1
fi

echo "Restauration depuis ${SRC} ..."
# --drop : remplace les collections existantes par celles de la sauvegarde
mongorestore --uri "$MONGODB_URI" --db "${DB_NAME:-dvf}" --drop "$SRC"
echo "Termine."
