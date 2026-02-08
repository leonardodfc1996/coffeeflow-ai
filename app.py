from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from datetime import datetime
import json
import os

app = Flask(__name__)
CORS(app)  # Allow requests from any origin

# In-memory storage (in production you'd use a database)
telemetry_data = []
MAX_DATA_POINTS = 100  # Keep only last 100 points

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    """Endpoint to verify server is running"""
    return jsonify({
        "status": "healthy",
        "service": "CoffeeFlow AI Backend",
        "timestamp": datetime.now().isoformat(),
        "data_points": len(telemetry_data),
        "version": "2.0.0"
    })

@app.route('/api/telemetry', methods=['POST'])
def receive_telemetry():
    """Receive telemetry data from robot"""
    try:
        data = request.json
        
        # Validate required data
        required_fields = ['robot_id', 'harvest_kg', 'battery', 'slope_degrees', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400
        
        # Add timestamp
        data['timestamp'] = datetime.now().isoformat()
        data['id'] = len(telemetry_data) + 1
        
        # Add to list
        telemetry_data.append(data)
        
        # Keep only last MAX_DATA_POINTS
        if len(telemetry_data) > MAX_DATA_POINTS:
            telemetry_data.pop(0)
        
        print(f"📡 Telemetry received from {data['robot_id']}: {data['harvest_kg']}kg at {data['location']}")
        
        return jsonify({
            "status": "success",
            "message": "Telemetry received",
            "id": data['id'],
            "timestamp": data['timestamp']
        })
        
    except Exception as e:
        print(f"❌ Error receiving telemetry: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/telemetry/latest', methods=['GET'])
def get_latest_telemetry():
    """Get latest telemetry data"""
    if not telemetry_data:
        return jsonify({"message": "No data yet"}), 404
    
    return jsonify(telemetry_data[-1])

@app.route('/api/telemetry/all', methods=['GET'])
def get_all_telemetry():
    """Get all telemetry data"""
    return jsonify(telemetry_data)

@app.route('/api/telemetry/clear', methods=['POST'])
def clear_telemetry():
    """Clear all data (development only)"""
    telemetry_data.clear()
    return jsonify({"status": "success", "message": "All telemetry data cleared"})

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get operation statistics"""
    if not telemetry_data:
        return jsonify({"message": "No data available"}), 404
    
    total_harvest = sum(item['harvest_kg'] for item in telemetry_data)
    avg_battery = sum(item['battery'] for item in telemetry_data) / len(telemetry_data)
    avg_slope = sum(item['slope_degrees'] for item in telemetry_data) / len(telemetry_data)
    
    return jsonify({
        "total_harvest_kg": round(total_harvest, 2),
        "average_battery": round(avg_battery, 2),
        "average_slope": round(avg_slope, 2),
        "total_data_points": len(telemetry_data),
        "first_timestamp": telemetry_data[0]['timestamp'] if telemetry_data else None,
        "last_timestamp": telemetry_data[-1]['timestamp'] if telemetry_data else None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
