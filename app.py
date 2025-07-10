#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
from pathlib import Path

app = Flask(__name__, static_folder='static')

def fix_image_url(image_url):
    """Fix image URL by adding /static/ prefix if needed"""
    if not image_url:
        return None
    if image_url.startswith('/static/'):
        return image_url
    if image_url.startswith('static/'):
        return '/' + image_url
    return '/static/' + image_url

def get_db_connection():
    """Create a database connection"""
    db_path = os.getenv('DATABASE_PATH', 'data/pals.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

@app.route('/')
def index():
    """Main page showing list of all pals"""
    conn = get_db_connection()
    
    # Get all pals with their elements
    query = """
    SELECT p.id, p.no, p.name, p.image_url, 
           GROUP_CONCAT(e.name) as elements
    FROM pal p
    LEFT JOIN pal_element pe ON p.id = pe.pal_id
    LEFT JOIN element e ON pe.element_id = e.id
    GROUP BY p.id
    ORDER BY p.no, p.name
    """
    
    pals = conn.execute(query).fetchall()
    conn.close()
    
    # Fix image URLs for all pals
    for pal in pals:
        pal = dict(pal)
        pal['image_url'] = fix_image_url(pal['image_url'])
    
    return render_template('index.html', pals=pals)

@app.route('/pal/<int:pal_id>')
def pal_detail(pal_id):
    """Show detailed information for a specific pal"""
    conn = get_db_connection()
    
    # Get pal basic info
    pal = conn.execute('SELECT * FROM pal WHERE id = ?', (pal_id,)).fetchone()
    
    if not pal:
        conn.close()
        return "Pal not found", 404
    
    # Get pal elements
    elements = conn.execute('''
        SELECT e.name 
        FROM element e
        JOIN pal_element pe ON e.id = pe.element_id
        WHERE pe.pal_id = ?
    ''', (pal_id,)).fetchall()
    
    # Get work suitabilities
    work_suitabilities = conn.execute('''
        SELECT s.name, ws.level
        FROM work_suitability ws
        JOIN suitability s ON ws.suitability_id = s.id
        WHERE ws.pal_id = ?
        ORDER BY ws.level DESC, s.name
    ''', (pal_id,)).fetchall()
    
    # Get breeding combinations where this pal is a parent
    breeding_as_parent = conn.execute('''
        SELECT p1.name as parent1_name, p2.name as parent2_name, c.name as child_name,
               c.id as child_id, c.image_url as child_image_url
        FROM breeding_combination bc
        JOIN pal p1 ON bc.parent1_id = p1.id
        JOIN pal p2 ON bc.parent2_id = p2.id
        JOIN pal c ON bc.child_id = c.id
        WHERE bc.parent1_id = ? OR bc.parent2_id = ?
        ORDER BY c.name
    ''', (pal_id, pal_id)).fetchall()
    
    # Get breeding combinations where this pal is a child
    breeding_as_child = conn.execute('''
        SELECT p1.name as parent1_name, p2.name as parent2_name,
               p1.id as parent1_id, p2.id as parent2_id,
               p1.image_url as parent1_image_url, p2.image_url as parent2_image_url
        FROM breeding_combination bc
        JOIN pal p1 ON bc.parent1_id = p1.id
        JOIN pal p2 ON bc.parent2_id = p2.id
        WHERE bc.child_id = ?
        ORDER BY p1.name, p2.name
    ''', (pal_id,)).fetchall()
    
    conn.close()
    
    # Fix image URLs
    pal = dict(pal)
    pal['image_url'] = fix_image_url(pal['image_url'])
    
    # Fix breeding combination image URLs
    breeding_as_parent = [dict(combo) for combo in breeding_as_parent]
    for combo in breeding_as_parent:
        combo['child_image_url'] = fix_image_url(combo['child_image_url'])
    
    breeding_as_child = [dict(combo) for combo in breeding_as_child]
    for combo in breeding_as_child:
        combo['parent1_image_url'] = fix_image_url(combo['parent1_image_url'])
        combo['parent2_image_url'] = fix_image_url(combo['parent2_image_url'])
    
    return render_template('pal_detail.html', 
                         pal=pal, 
                         elements=elements,
                         work_suitabilities=work_suitabilities,
                         breeding_as_parent=breeding_as_parent,
                         breeding_as_child=breeding_as_child)

@app.route('/api/pals')
def api_pals():
    """API endpoint to get all pals as JSON"""
    conn = get_db_connection()
    
    query = """
    SELECT p.id, p.no, p.name, p.image_url, 
           GROUP_CONCAT(e.name) as elements
    FROM pal p
    LEFT JOIN pal_element pe ON p.id = pe.pal_id
    LEFT JOIN element e ON pe.element_id = e.id
    GROUP BY p.id
    ORDER BY p.no, p.name
    """
    
    pals = conn.execute(query).fetchall()
    conn.close()
    
    # Convert to list of dictionaries
    pals_list = []
    for pal in pals:
        pals_list.append({
            'id': pal['id'],
            'no': pal['no'],
            'name': pal['name'],
            'image_url': fix_image_url(pal['image_url']),
            'elements': pal['elements'].split(',') if pal['elements'] else []
        })
    
    return jsonify(pals_list)

@app.route('/api/pal/<int:pal_id>')
def api_pal_detail(pal_id):
    """API endpoint to get detailed pal information as JSON"""
    conn = get_db_connection()
    
    # Get pal basic info
    pal = conn.execute('SELECT * FROM pal WHERE id = ?', (pal_id,)).fetchone()
    
    if not pal:
        conn.close()
        return jsonify({'error': 'Pal not found'}), 404
    
    # Get pal elements
    elements = conn.execute('''
        SELECT e.name 
        FROM element e
        JOIN pal_element pe ON e.id = pe.element_id
        WHERE pe.pal_id = ?
    ''', (pal_id,)).fetchall()
    
    # Get work suitabilities
    work_suitabilities = conn.execute('''
        SELECT s.name, ws.level
        FROM work_suitability ws
        JOIN suitability s ON ws.suitability_id = s.id
        WHERE ws.pal_id = ?
        ORDER BY ws.level DESC, s.name
    ''', (pal_id,)).fetchall()
    
    conn.close()
    
    return jsonify({
        'id': pal['id'],
        'no': pal['no'],
        'name': pal['name'],
        'image_url': fix_image_url(pal['image_url']),
        'elements': [e['name'] for e in elements],
        'work_suitabilities': [{'name': ws['name'], 'level': ws['level']} for ws in work_suitabilities]
    })

@app.route('/api/breeding-combinations', methods=['POST'])
def api_breeding_combinations():
    """API endpoint to get breeding combinations for selected pals"""
    data = request.get_json()
    pal_ids = data.get('pal_ids', [])
    
    if len(pal_ids) < 2:
        return jsonify({'error': 'At least 2 pals are required'}), 400
    
    conn = get_db_connection()
    
    # Get all breeding combinations between the selected pals
    placeholders = ','.join(['?' for _ in pal_ids])
    query = '''
        SELECT DISTINCT
            p1.id as parent1_id, p1.name as parent1_name, p1.image_url as parent1_image_url,
            p2.id as parent2_id, p2.name as parent2_name, p2.image_url as parent2_image_url,
            c.id as child_id, c.name as child_name, c.image_url as child_image_url, c.no as child_no
        FROM breeding_combination bc
        JOIN pal p1 ON bc.parent1_id = p1.id
        JOIN pal p2 ON bc.parent2_id = p2.id
        JOIN pal c ON bc.child_id = c.id
        WHERE (p1.id IN ({}) AND p2.id IN ({}))
        ORDER BY c.name
    '''.format(placeholders, placeholders)
    
    # Execute query with pal_ids twice (for both parent1 and parent2)
    params = pal_ids + pal_ids
    combinations = conn.execute(query, params).fetchall()
    
    conn.close()
    
    # Convert to list of dictionaries
    combinations_list = []
    for combo in combinations:
        combinations_list.append({
            'parent1': {
                'id': combo['parent1_id'],
                'name': combo['parent1_name'],
                'image_url': fix_image_url(combo['parent1_image_url'])
            },
            'parent2': {
                'id': combo['parent2_id'],
                'name': combo['parent2_name'],
                'image_url': fix_image_url(combo['parent2_image_url'])
            },
            'child': {
                'id': combo['child_id'],
                'name': combo['child_name'],
                'image_url': fix_image_url(combo['child_image_url']),
                'no': combo['child_no']
            }
        })
    
    return jsonify({
        'combinations': combinations_list,
        'total_combinations': len(combinations_list)
    })

@app.route('/api/check-breedable-pal', methods=['POST'])
def api_check_breedable_pal():
    """API endpoint to check if a specific pal can be bred from selected pals"""
    data = request.get_json()
    pal_ids = data.get('pal_ids', [])
    target_pal_id = data.get('target_pal_id')
    
    if len(pal_ids) < 2:
        return jsonify({'error': 'At least 2 pals are required'}), 400
    
    if not target_pal_id:
        return jsonify({'error': 'Target pal ID is required'}), 400
    
    conn = get_db_connection()
    
    # Get all pals for reference
    all_pals = {}
    pals_query = "SELECT id, name, image_url, no FROM pal"
    for pal in conn.execute(pals_query).fetchall():
        all_pals[pal['id']] = {
            'id': pal['id'],
            'name': pal['name'],
            'image_url': fix_image_url(pal['image_url']),
            'no': pal['no']
        }
    
    # Check if target pal exists
    if target_pal_id not in all_pals:
        conn.close()
        return jsonify({'error': 'Target pal not found'}), 404
    
    target_pal = all_pals[target_pal_id]
    
    # Simulate breeding steps to find if target pal can be bred
    available_pals = set(pal_ids)
    all_combinations = []  # Store all combinations for all steps
    max_steps = 10  # Prevent infinite loops
    step = 0
    found = False
    
    while step < max_steps:
        step += 1
        new_combinations = []
        
        # Get all possible breeding combinations with current available pals
        placeholders = ','.join(['?' for _ in available_pals])
        query = '''
            SELECT DISTINCT
                p1.id as parent1_id, p2.id as parent2_id,
                c.id as child_id
            FROM breeding_combination bc
            JOIN pal p1 ON bc.parent1_id = p1.id
            JOIN pal p2 ON bc.parent2_id = p2.id
            JOIN pal c ON bc.child_id = c.id
            WHERE (p1.id IN ({}) AND p2.id IN ({}))
        '''.format(placeholders, placeholders)
        
        params = list(available_pals) + list(available_pals)
        combinations = conn.execute(query, params).fetchall()
        
        for combo in combinations:
            child_id = combo['child_id']
            parent1_id = combo['parent1_id']
            parent2_id = combo['parent2_id']
            
            # Check if this is a new combination (child not already available)
            if child_id not in available_pals:
                new_combinations.append({
                    'step': step,
                    'parent1': all_pals[parent1_id],
                    'parent2': all_pals[parent2_id],
                    'child': all_pals[child_id]
                })
                
                # Add child to available pals
                available_pals.add(child_id)
                
                # If this is the target, mark as found
                if child_id == target_pal_id:
                    found = True
        
        all_combinations.extend(new_combinations)
        
        # If found, break
        if found:
            break
        # If no new combinations found, we can't breed the target
        if not new_combinations:
            break
    
    conn.close()
    
    if found:
        # Recursively build the full path to the target
        full_path = build_full_breeding_path(target_pal_id, all_combinations, set(pal_ids))
        return jsonify({
            'breedable': True,
            'target_pal': target_pal,
            'breeding_path': full_path,
            'steps_required': len(full_path)
        })
    else:
        return jsonify({
            'breedable': False,
            'target_pal': target_pal,
            'message': 'Target pal cannot be bred from the selected pals'
        })

def build_full_breeding_path(target_id, all_combinations, initial_pals):
    """Recursively build the full breeding path to the target pal as an ordered list of steps."""
    path = []
    combo = next((c for c in all_combinations if c['child']['id'] == target_id), None)
    if not combo:
        return []
    # Recursively add parent1 path if not in initial
    if combo['parent1']['id'] not in initial_pals:
        path += build_full_breeding_path(combo['parent1']['id'], all_combinations, initial_pals)
    # Recursively add parent2 path if not in initial
    if combo['parent2']['id'] not in initial_pals:
        path += build_full_breeding_path(combo['parent2']['id'], all_combinations, initial_pals)
    # Add this step
    path.append(combo)
    return path

@app.route('/breeder')
def breeder():
    """Breeding calculator page"""
    conn = get_db_connection()
    
    # Get all pals for the selection dropdown
    pals = conn.execute('''
        SELECT p.id, p.name, p.image_url, p.no,
               GROUP_CONCAT(e.name) as elements
        FROM pal p
        LEFT JOIN pal_element pe ON p.id = pe.pal_id
        LEFT JOIN element e ON pe.element_id = e.id
        WHERE p.no != -1  -- Exclude special pals
        GROUP BY p.id
        ORDER BY p.no, p.name
    ''').fetchall()
    
    # Convert no to string and fix image URLs
    formatted_pals = []
    for pal in pals:
        pal_dict = dict(pal)
        pal_dict['no'] = str(pal_dict['no']) if pal_dict['no'] else ''
        pal_dict['image_url'] = fix_image_url(pal_dict['image_url'])
        formatted_pals.append(pal_dict)
    
    conn.close()
    return render_template('breeder.html', pals=formatted_pals)

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files (images) with optimization headers"""
    response = send_from_directory(app.static_folder, filename)
    
    # Add caching headers for images
    if filename.lower().endswith(('.webp', '.png', '.jpg', '.jpeg')):
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
        response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
    
    return response

if __name__ == '__main__':
    # Check if database exists
    db_path = os.getenv('DATABASE_PATH', 'data/pals.db')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Please run the container first to create the database.")
        exit(1)
    
    print(f"Starting Flask app...")
    print(f"Database: {db_path}")
    print(f"Open your browser to: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000) 