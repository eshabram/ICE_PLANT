#!/bin/bash
# Usage: ./extract_eduroam_certs.sh eduroam.mobileconfig

set -e

INPUT="$1"
OUTDIR="certs_extracted"
mkdir -p "$OUTDIR"

echo "[*] Decoding $INPUT to plist ..."
security cms -D -i "$INPUT" -o "$OUTDIR/profile.plist"

echo "[*] Extracting certificates ..."
i=1
grep -A9999 "<data>" "$OUTDIR/profile.plist" | \
  sed -n '/<data>/,/<\/data>/p' | \
  sed -e 's/<\/\?data>//g' -e 's/ //g' | \
  awk 'NF {print} /^<\/data>$/ {print ""}' | \
  while read -r line; do
    if [ -z "$line" ]; then
      if [ -s "$OUTDIR/cert${i}.b64" ]; then
        echo "  - Converting $OUTDIR/cert${i}.b64 -> $OUTDIR/cert${i}.pem"
        base64 -D -i "$OUTDIR/cert${i}.b64" -o "$OUTDIR/cert${i}.der"
        openssl x509 -inform DER -in "$OUTDIR/cert${i}.der" -out "$OUTDIR/cert${i}.pem" || true
        i=$((i+1))
      fi
    else
      echo "$line" >> "$OUTDIR/cert${i}.b64"
    fi
  done

# Combine into one PEM
cat "$OUTDIR"/*.pem > "$OUTDIR/ucdavis_eduroam.pem" 2>/dev/null || true

echo "[*] Combined PEM: $OUTDIR/ucdavis_eduroam.pem"
