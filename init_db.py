#!/usr/bin/env python3
import sqlite3
import os
import sys
import json
from pathlib import Path

def create_database():
    """Create the database and all tables"""
    
    # Get database path from environment or use default
    db_path = os.getenv('DATABASE_PATH', 'pals.db')
    
    print(f"Creating database at: {db_path}")
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create tables
        
        # Element table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS element (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Suitability table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suitability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        ''')
        
        # Pal table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                no TEXT NOT NULL,
                name TEXT NOT NULL,
                image_url TEXT
            )
        ''')
        
        # Pal-Element relationship table (many-to-many)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pal_element (
                pal_id INTEGER NOT NULL,
                element_id INTEGER NOT NULL,
                PRIMARY KEY (pal_id, element_id),
                FOREIGN KEY (pal_id) REFERENCES pal (id) ON DELETE CASCADE,
                FOREIGN KEY (element_id) REFERENCES element (id) ON DELETE CASCADE
            )
        ''')
        
        # Work Suitability table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS work_suitability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pal_id INTEGER NOT NULL,
                suitability_id INTEGER NOT NULL,
                level INTEGER NOT NULL CHECK (level >= 1 AND level <= 5),
                FOREIGN KEY (pal_id) REFERENCES pal (id) ON DELETE CASCADE,
                FOREIGN KEY (suitability_id) REFERENCES suitability (id) ON DELETE CASCADE,
                UNIQUE(pal_id, suitability_id)
            )
        ''')
        
        # Breeding Combination table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breeding_combination (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent1_id INTEGER NOT NULL,
                parent2_id INTEGER NOT NULL,
                child_id INTEGER NOT NULL,
                FOREIGN KEY (parent1_id) REFERENCES pal (id) ON DELETE CASCADE,
                FOREIGN KEY (parent2_id) REFERENCES pal (id) ON DELETE CASCADE,
                FOREIGN KEY (child_id) REFERENCES pal (id) ON DELETE CASCADE,
                UNIQUE(parent1_id, parent2_id)
            )
        ''')
        
        # Load data from JSON files
        load_data_from_json(cursor)
        
        # Commit changes
        conn.commit()
        print("Database created successfully!")
        
        # Show table information
        show_database_info(cursor)
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

def load_data_from_json(cursor):
    """Load data from JSON files"""
    
    data_dir = Path("data")
    if not data_dir.exists():
        print(f"Warning: {data_dir} directory not found. Please create it and add your JSON data files.")
        return
    
    # Load elements
    elements_file = data_dir / "elements.json"
    if elements_file.exists():
        print(f"Loading elements from {elements_file}")
        with open(elements_file, 'r', encoding='utf-8') as f:
            elements_data = json.load(f)
            for element in elements_data:
                cursor.execute('INSERT OR IGNORE INTO element (name) VALUES (?)', (element['name'],))
        print(f"Loaded {len(elements_data)} elements")
    else:
        print(f"Warning: {elements_file} not found, skipping elements")
    
    # Load suitabilities
    suitabilities_file = data_dir / "suitabilities.json"
    if suitabilities_file.exists():
        print(f"Loading suitabilities from {suitabilities_file}")
        with open(suitabilities_file, 'r', encoding='utf-8') as f:
            suitabilities_data = json.load(f)
            for suitability in suitabilities_data:
                cursor.execute('INSERT OR IGNORE INTO suitability (name) VALUES (?)', (suitability['name'],))
        print(f"Loaded {len(suitabilities_data)} suitabilities")
    else:
        print(f"Warning: {suitabilities_file} not found, skipping suitabilities")
    
    # Load pals
    pals_file = data_dir / "pals.json"
    if pals_file.exists():
        print(f"Loading pals from {pals_file}")
        with open(pals_file, 'r', encoding='utf-8') as f:
            pals_data = json.load(f)
            for pal in pals_data:
                cursor.execute(
                    'INSERT OR IGNORE INTO pal (no, name, image_url) VALUES (?, ?, ?)',
                    (pal.get('no'), pal['name'], pal.get('image_url'))
                )
        print(f"Loaded {len(pals_data)} pals")
    else:
        print(f"Warning: {pals_file} not found, skipping pals")
    
    # Load pal-elements relationships
    pal_elements_file = data_dir / "pal_elements.json"
    if pal_elements_file.exists():
        print(f"Loading pal-elements from {pal_elements_file}")
        with open(pal_elements_file, 'r', encoding='utf-8') as f:
            pal_elements_data = json.load(f)
            for rel in pal_elements_data:
                # Get pal_id by name
                cursor.execute('SELECT id FROM pal WHERE name = ?', (rel['pal_name'],))
                pal_result = cursor.fetchone()
                if pal_result:
                    pal_id = pal_result[0]
                    # Get element_id by name
                    cursor.execute('SELECT id FROM element WHERE name = ?', (rel['element_name'],))
                    element_result = cursor.fetchone()
                    if element_result:
                        element_id = element_result[0]
                        cursor.execute('INSERT OR IGNORE INTO pal_element (pal_id, element_id) VALUES (?, ?)', 
                                     (pal_id, element_id))
        print(f"Loaded {len(pal_elements_data)} pal-element relationships")
    else:
        print(f"Warning: {pal_elements_file} not found, skipping pal-elements")
    
    # Load work suitabilities
    work_suitabilities_file = data_dir / "work_suitabilities.json"
    if work_suitabilities_file.exists():
        print(f"Loading work suitabilities from {work_suitabilities_file}")
        with open(work_suitabilities_file, 'r', encoding='utf-8') as f:
            work_suitabilities_data = json.load(f)
            for ws in work_suitabilities_data:
                # Get pal_id by name
                cursor.execute('SELECT id FROM pal WHERE name = ?', (ws['pal_name'],))
                pal_result = cursor.fetchone()
                if pal_result:
                    pal_id = pal_result[0]
                    # Get suitability_id by name
                    cursor.execute('SELECT id FROM suitability WHERE name = ?', (ws['suitability_name'],))
                    suitability_result = cursor.fetchone()
                    if suitability_result:
                        suitability_id = suitability_result[0]
                        cursor.execute('INSERT OR IGNORE INTO work_suitability (pal_id, suitability_id, level) VALUES (?, ?, ?)', 
                                     (pal_id, suitability_id, ws['level']))
        print(f"Loaded {len(work_suitabilities_data)} work suitabilities")
    else:
        print(f"Warning: {work_suitabilities_file} not found, skipping work suitabilities")
    
    # Load breeding combinations
    breeding_combinations_file = data_dir / "breeding_combinations.json"
    if breeding_combinations_file.exists():
        print(f"Loading breeding combinations from {breeding_combinations_file}")
        with open(breeding_combinations_file, 'r', encoding='utf-8') as f:
            breeding_combinations_data = json.load(f)
            for bc in breeding_combinations_data:
                # Get parent1_id by name
                cursor.execute('SELECT id FROM pal WHERE name = ?', (bc['parent1_name'],))
                parent1_result = cursor.fetchone()
                # Get parent2_id by name
                cursor.execute('SELECT id FROM pal WHERE name = ?', (bc['parent2_name'],))
                parent2_result = cursor.fetchone()
                # Get child_id by name
                cursor.execute('SELECT id FROM pal WHERE name = ?', (bc['child_name'],))
                child_result = cursor.fetchone()
                
                if parent1_result and parent2_result and child_result:
                    cursor.execute('INSERT OR IGNORE INTO breeding_combination (parent1_id, parent2_id, child_id) VALUES (?, ?, ?)', 
                                 (parent1_result[0], parent2_result[0], child_result[0]))
        print(f"Loaded {len(breeding_combinations_data)} breeding combinations")
    else:
        print(f"Warning: {breeding_combinations_file} not found, skipping breeding combinations")

def show_database_info(cursor):
    """Show information about the created database"""
    
    print("\n=== Database Schema ===")
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            pk_str = " PRIMARY KEY" if pk else ""
            not_null_str = " NOT NULL" if not_null else ""
            print(f"  - {col_name} ({col_type}){not_null_str}{pk_str}")
    
    print("\n=== Data Counts ===")
    
    # Count records in each table
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"{table_name}: {count} records")

if __name__ == "__main__":
    create_database() 