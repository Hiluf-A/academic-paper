from flask import Flask, render_template, jsonify, request
from database.db_manager import DatabaseManager
import os

app = Flask(__name__)
db = DatabaseManager()

@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('index.html')

@app.route('/api/violations')
def get_violations():
    """Get recent violations"""
    violations = db.get_violations(limit=10)
    return jsonify(violations)

@app.route('/api/top-speeders')
def get_top_speeders():
    """Get top speeders"""
    speeders = db.get_top_speeders(limit=5)
    return jsonify(speeders)

# --- CRUD for Drivers ---
@app.route('/api/drivers', methods=['GET'])
def list_drivers():
    drivers = db.get_all_drivers() if hasattr(db, 'get_all_drivers') else []
    return jsonify(drivers)

@app.route('/api/drivers', methods=['POST'])
def create_driver():
    data = request.json
    name = data.get('name')
    license_plate = data.get('license_plate')
    email = data.get('email')
    if not (name and license_plate and email):
        return jsonify({'error': 'Missing fields'}), 400
    success = db.add_driver(name, license_plate, email)
    if success:
        return jsonify({'message': 'Driver added successfully'}), 201
    else:
        return jsonify({'error': 'Driver already exists or error occurred'}), 400

@app.route('/api/drivers/<license_plate>', methods=['PUT'])
def update_driver(license_plate):
    data = request.json
    name = data.get('name')
    email = data.get('email')
    success = db.update_driver(license_plate, name, email) if hasattr(db, 'update_driver') else False
    if success:
        return jsonify({'message': 'Driver updated successfully'})
    else:
        return jsonify({'error': 'Driver not found or error occurred'}), 404

@app.route('/api/drivers/<license_plate>', methods=['DELETE'])
def delete_driver(license_plate):
    success = db.delete_driver(license_plate) if hasattr(db, 'delete_driver') else False
    if success:
        return jsonify({'message': 'Driver deleted successfully'})
    else:
        return jsonify({'error': 'Driver not found or error occurred'}), 404

# --- CRUD for Violations (Delete only) ---
@app.route('/api/violations/<int:violation_id>', methods=['DELETE'])
def delete_violation(violation_id):
    success = db.delete_violation(violation_id) if hasattr(db, 'delete_violation') else False
    if success:
        return jsonify({'message': 'Violation deleted successfully'})
    else:
        return jsonify({'error': 'Violation not found or error occurred'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 