# Pals Database Container

A Podman container with a SQLite database for managing Pals, Elements, Suitabilities, and Breeding Combinations.

## Database Schema

### Tables

1. **pal** - Main Pal entity
   - `id` (PRIMARY KEY)
   - `no` (INTEGER, can be -1, else unique)
   - `name` (TEXT, NOT NULL)
   - `image_url` (TEXT)

2. **element** - Element types
   - `id` (PRIMARY KEY)
   - `name` (TEXT, NOT NULL, UNIQUE)

3. **suitability** - Work suitability types
   - `id` (PRIMARY KEY)
   - `name` (TEXT, NOT NULL, UNIQUE)

4. **pal_element** - Many-to-many relationship between Pals and Elements
   - `pal_id` (FOREIGN KEY to pal.id)
   - `element_id` (FOREIGN KEY to element.id)

5. **work_suitability** - Work suitability levels for Pals
   - `id` (PRIMARY KEY)
   - `pal_id` (FOREIGN KEY to pal.id)
   - `suitability_id` (FOREIGN KEY to suitability.id)
   - `level` (INTEGER, 1-5)

6. **breeding_combination** - Breeding combinations
   - `id` (PRIMARY KEY)
   - `parent1_id` (FOREIGN KEY to pal.id)
   - `parent2_id` (FOREIGN KEY to pal.id)
   - `child_id` (FOREIGN KEY to pal.id)

## Quick Start

### Prerequisites
- Podman installed on your system
- Python 3 installed on your system
- Bash shell

### Running the Database

1. **Make the run script executable:**
   ```bash
   chmod +x run.sh
   ```

2. **Run the initialization script:**
   ```bash
   ./run.sh
   ```

This will:
- Build the Podman container
- Run the container to initialize the database from JSON files
- Create the database file at `./data/pals.db`
- Show a preview of the database contents

**Note:** You need to create the `./data/` directory and add your JSON files before running the container.

### Running the Web Application

#### Option 1: Local Python Installation
1. **Make the app script executable:**
   ```bash
   chmod +x run_app.sh
   ```

2. **Run the web application:**
   ```bash
   ./run_app.sh
   ```

#### Option 2: Containerized Web Application
1. **Make the web script executable:**
   ```bash
   chmod +x run_web.sh
   ```

2. **Run the web application in container:**
   ```bash
   ./run_web.sh
   ```

#### Option 3: Full Containerized Solution (Database + Web App)
1. **Make the full script executable:**
   ```bash
   chmod +x run_full.sh
   ```

2. **Run everything in containers:**
   ```bash
   ./run_full.sh
   ```

3. **Open your browser to:** http://localhost:5000

The web application provides:
- A beautiful grid view of all pals
- Search functionality
- Detailed pal information pages
- Work suitability levels with color coding
- Breeding combination information
- Responsive design for mobile and desktop

### Manual Steps

If you prefer to run the commands manually:

1. **Build the container:**
   ```bash
   podman build -t pals-db .
   ```

2. **Run the container:**
   ```bash
   podman run --rm -v "$(pwd)/data:/app/data" pals-db
   ```

## Database Operations

### View Database Contents

If you have `sqlite3` installed:

```bash
# Connect to the database
sqlite3 ./data/pals.db

# View all pals
SELECT * FROM pal;

# View pals with their elements
SELECT p.name, GROUP_CONCAT(e.name) as elements
FROM pal p
LEFT JOIN pal_element pe ON p.id = pe.pal_id
LEFT JOIN element e ON pe.element_id = e.id
GROUP BY p.id;

# View work suitabilities
SELECT p.name, s.name as suitability, ws.level
FROM work_suitability ws
JOIN pal p ON ws.pal_id = p.id
JOIN suitability s ON ws.suitability_id = s.id;
```

### Add New Data

You can modify the `init_db.py` script to add more sample data, or use SQLite commands directly:

```bash
sqlite3 ./data/pals.db
```

## Container Details

- **Base Image:** Python 3.11-slim
- **Database:** SQLite
- **Database Location:** `/app/data/pals.db` (inside container)
- **Mounted Volume:** `./data` (host) → `/app/data` (container)
- **Web Application:** Flask app included in container
- **Port:** 5000 (exposed for web app)

## Web Application Details

- **Framework:** Flask
- **Port:** 5000
- **Features:** Responsive web interface, search, detailed views
- **Dependencies:** Flask, Werkzeug
- **Templates:** Bootstrap 5, Font Awesome icons
- **Container Support:** Can run both database init and web app

## Data Files

The system uses JSON files in the `./data/` directory to populate the database:

- **`elements.json`** - List of element types
- **`suitabilities.json`** - List of work suitability types  
- **`pals.json`** - List of all pals with their basic information
- **`pal_elements.json`** - Relationships between pals and their elements
- **`work_suitabilities.json`** - Work suitability levels for each pal
- **`breeding_combinations.json`** - Breeding combinations between pals

## Customization

To modify the database schema or add more data:

### Adding New Data
1. Edit the appropriate JSON file in the `./data/` directory
2. Rebuild the container: `podman build -t pals-db .`
3. Run the container again to reinitialize the database

### JSON File Formats

**elements.json:**
```json
[
  {"name": "Fire"},
  {"name": "Water"}
]
```

**pals.json:**
```json
[
  {"no": 1, "name": "Lamball", "image_url": "https://example.com/lamball.jpg"},
  {"no": -1, "name": "Unknown Pal", "image_url": "https://example.com/unknown.jpg"}
]
```

**pal_elements.json:**
```json
[
  {"pal_name": "Lamball", "element_name": "Normal"},
  {"pal_name": "Cattiva", "element_name": "Fire"}
]
```

**work_suitabilities.json:**
```json
[
  {"pal_name": "Lamball", "suitability_name": "Handiwork", "level": 1},
  {"pal_name": "Cattiva", "suitability_name": "Gathering", "level": 2}
]
```

**breeding_combinations.json:**
```json
[
  {"parent1_name": "Lamball", "parent2_name": "Cattiva", "child_name": "Chikipi"}
]
```

### Modifying Schema
To change the database schema:
1. Edit `init_db.py`
2. Rebuild the container: `podman build -t pals-db .`
3. Run the container again to reinitialize the database 