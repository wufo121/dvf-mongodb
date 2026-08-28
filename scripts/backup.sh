#!/usr/bin/env bash
# Sauvegarde de la base DVF (livrable 6).
# L'URI est lue depuis .env : jamais d'identifiant en clair dans ce script.
#
# Usage : ./scripts/backup.sh
set -euo pipefail

# Charge les variables du .env (situe a la racine du projet)
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

if [ -z "${MONGODB_URI:-}" ]; then
  echo "MONGODB_URI absent. Copiez .env.example en .env." >&2
  exit 1
fi

HORODATAGE=$(date +%Y%m%d_%H%M%S)
DEST="backups/${DB_NAME:-dvf}_${HORODATAGE}"

echo "Sauvegarde vers ${DEST} ..."
mongodump --uri "$MONGODB_URI" --db "${DB_NAME:-dvf}" --out "$DEST"
echo "Termine. Contenu :"
ls -R "$DEST"
