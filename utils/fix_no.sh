#!/bin/bash

# Input JSON file
INPUT="data/pals.json"
OUTPUT="data/pals.json"  # Overwrite in-place

# Use jq to convert all "no" values to strings
jq 'map(if has("no") then .no |= tostring else . end)' "$INPUT" > tmp.json && mv tmp.json "$OUTPUT"

echo "✅ Converted all 'no' fields to strings in $OUTPUT"
