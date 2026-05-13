import json
import time
import os
from threading import Thread
from flask import Flask, jsonify, request, render_template
from src.services import bus_stop_information_service
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    app = Flask(__name__)

    busStopInformationService = bus_stop_information_service.BusStopInformationService()

    @app.route('/api/timetable', methods=['POST'])
    def get_timetable():
        balle = json.loads(request.data)
        busStopInformation = busStopInformationService.GetBusStopInformation(balle)
        
        return jsonify([bus_stop.to_dict() for bus_stop in busStopInformation])


    # Main route to render the page
    @app.route('/')
    def index():
        return render_template('/timetable.html')

    # Main route to render the page
    @app.route('/v2')
    def v2():
        return render_template('/timetable_v2.html')

    app.run(debug=True)
        
        

if __name__ == '__main__':
    main()
 