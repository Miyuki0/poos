#!/bin/bash

# I use the data from https://game8.co/api/tool_structural_mappings/192.json?updatedAt=1750911923
# and save it to data/raw_data.txt

RAW_DATA_TXT="./data/raw_data.txt"
RAW_DATA_JSON="./data/raw_data.json"
CLEAN_DATA_JSON="./data/clean_data.json"

# first remove trailing backslash
sed -i 's/\\//g' $RAW_DATA_TXT

first=$(head -c 1 "$RAW_DATA_TXT")
last=$(tail -c 1 "$RAW_DATA_TXT")

if [[ ( "$first" == "$last" ) && ( "$first" == "'" || "$first" == '"' ) ]]; then
    tail -c +2 "$RAW_DATA_TXT" | head -c -1 > tmp && mv tmp "$RAW_DATA_TXT"
fi

# create a json file
cp $RAW_DATA_TXT $RAW_DATA_JSON

# remove unnecessary fields
jq 'walk(if type == "object" then del(.id, .url, .sortNum) else . end)' $RAW_DATA_JSON > $CLEAN_DATA_JSON

# create new mapping file
jq '[.combinationArraySchema.combinations[] | {
  "parent1_name": .parent1Name,
  "parent2_name": .parent2Name,
  "child_name": .childName
}]' "$CLEAN_DATA_JSON" > data/breeding_combinations.json