#!/bin/bash

# Exit on error
set -e

echo "🔍 Processing pals and images..."

# Step 1: Normalize image filenames in static/ directory
for image in static/*; do
    filename=$(basename "$image")
    ext="${filename##*.}"
    name="${filename%.*}"

    new_name="$name"

    # Remove 300px- prefix
    if [[ $name == 300px-* ]]; then
        new_name="${new_name#300px-}"
    fi

    # Remove _icon suffix
    new_name="${new_name%%_icon*}"

    # Only rename if the name changed
    if [[ "$name" != "$new_name" ]]; then
        echo "🧹 Renaming: $filename → $new_name.$ext"
        mv "$image" "static/$new_name.$ext"
    fi
done

# Refresh image list
images=$(ls static)

# Step 2: Update pals.json with matching image URLs
echo "📝 Updating pals.json..."

updated_pals="["
first=true

while read -r pal; do
    pal_name=$(echo "$pal" | jq -r '.name')
    pal_name_lower=$(echo "$pal_name" | tr '[:upper:]' '[:lower:]')
    image_name=$(echo "$pal_name_lower" | tr ' ' '_')

    matching_image=""
    for image in $images; do
        image_lower=$(echo "$image" | tr '[:upper:]' '[:lower:]')
        image_no_ext="${image_lower%.*}"

        if [[ "$image_no_ext" == "$image_name" ]]; then
            matching_image="$image"
            break
        fi
    done

    if [[ -n "$matching_image" ]]; then
        updated_pal=$(echo "$pal" | jq --arg url "static/$matching_image" '.image_url = $url')
        echo "✅ Matched: $pal_name → static/$matching_image"
    else
        updated_pal="$pal"
        echo "❌ No image found for: $pal_name"
    fi

    if [[ "$first" == "true" ]]; then
        updated_pals="$updated_pals$updated_pal"
        first=false
    else
        updated_pals="$updated_pals,$updated_pal"
    fi
done < <(jq -c '.[]' data/pals.json)

updated_pals="$updated_pals]"

# Step 3: Write the updated JSON back to the file
echo "$updated_pals" | jq '.' > data/pals.json

echo "✅ pals.json successfully updated!"
