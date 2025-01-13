from threading import Thread, Event
import time
from flask import Flask, render_template, jsonify
import requests
import json
from datetime import datetime, timedelta, timezone

class BusStops:
    def __init__(self,quayId,stopName):
        self.quayId = quayId
        self.stopName = stopName
        self.BusEntries = []

    def to_dict(self):
        # Convert the BusStops object into a dictionary
        return {
            'quayId': self.quayId,
            'stopName': self.stopName,
            'BusEntries': [entry.to_dict() for entry in self.BusEntries]  # Convert each BusEntry object in BusEntries list to dictionary
        }


class BusEntry:
    def __init__(self,line,destination,estArrival,hereIn,busStopName):
        self.busStopName = busStopName  # Bus-stop
        self.line = line                # Bus-line (eg. 22)
        self.destination = destination  # Destination (eg. Tyholt via .....)
        self.estArrival = estArrival    # Excpected arrival time
        self.hereIn = hereIn            # Time to arrive, in minutes or HH:MM time

    def to_dict(self):
        # Convert the BusEntry object into a dictionary
        return {
            'busStopName': self.busStopName,
            'line': self.line,
            'destination': self.destination,
            'estArrival': self.estArrival,
            'hereIn': self.hereIn
        }


class BusStopInformationService:    

    def __init__(self):

        config = ''.join(open("config.json","r").readlines())
        self.jsonConfig = json.loads(config)
        with open("output.json", "r") as input:  # Using 'a' mode for appending
            content = ''.join(input.readlines())
            quayArray = json.loads(content)
            self.busStops = quayArray
        pass

    def GetBusStopInformation(self):
        current_datetime = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        configuration = self.jsonConfig
        headers = configuration['clientName']

        configBusStops = [ReplaceUnknownCharacters(busstop) for busstop in configuration['busStops']]

        busStopQuays = GetStopPlaceByName(self.busStops, configBusStops)

        print(f"Finding bus stops near {', '.join(configBusStops)}..")

        newstops = [quay['id'] for quay in busStopQuays]
        
        data = { 
            "operationName": "getDeparturesForQuays",
            "variables": {
                "ids": newstops,
                "arrivalDeparture": "departures",
                "numberOfDepartures": int(configuration['maxResultsToGet']),
                "travelDate": current_datetime,
                "lines": []
                },
                "query": "query getDeparturesForQuays($ids: [String!]!, $numberOfDepartures: Int, $arrivalDeparture: ArrivalDeparture, $travelDate: DateTime, $lines: [ID]) {\n  quays(ids: $ids) {\n    id\n    estimatedCalls(\n      arrivalDeparture: $arrivalDeparture\n      includeCancelledTrips: true\n      numberOfDepartures: $numberOfDepartures\n      startTime: $travelDate\n      whiteListed: {lines: $lines}\n    ) {\n      date\n      aimedArrivalTime\n      aimedDepartureTime\n      bookingArrangements {\n        latestBookingTime\n        latestBookingDay\n        minimumBookingPeriod\n        bookingNote\n        bookWhen\n        bookingContact {\n          contactPerson\n          email\n          url\n          phone\n          furtherDetails\n          __typename\n        }\n        __typename\n      }\n      serviceJourney {\n        id\n        journeyPattern {\n          line {\n            id\n            publicCode\n            __typename\n          }\n          __typename\n        }\n        notices {\n          id\n          text\n          __typename\n        }\n        transportMode\n        transportSubmode\n        __typename\n      }\n      cancellation\n      expectedArrivalTime\n      expectedDepartureTime\n      destinationDisplay {\n        frontText\n        via\n        __typename\n      }\n      notices {\n        id\n        text\n        __typename\n      }\n      predictionInaccurate\n      quay {\n        id\n        name\n        description\n        publicCode\n        stopPlace {\n          name\n          description\n          __typename\n        }\n        __typename\n      }\n      realtime\n      situations {\n        situationNumber\n        summary {\n          value\n          language\n          __typename\n        }\n        description {\n          value\n          language\n          __typename\n        }\n        advice {\n          value\n          language\n          __typename\n        }\n        validityPeriod {\n          startTime\n          endTime\n          __typename\n        }\n        reportType\n        infoLinks {\n          uri\n          label\n          __typename\n        }\n        __typename\n      }\n      occupancyStatus\n      __typename\n    }\n    __typename\n  }\n}"
            }

        # Request data for getting specific bus line
        
        response = requests.post(configuration['baseUrl'], json=data, headers=headers)
        
        print(f'Status Code: {response.status_code}')
        
        if response.status_code != 200: 
            raise Exception("HTTP request did not result in 200 OK")
        
        content = response.json()
        
        busDeparturesFinal = []

        busStops = content['data']['quays']
        
        for busStop in busStops:
            quayId = busStop['id']
            
            busFilter = configuration['busFilter']
            
            filterValues = configuration['busFilter']['values']

            departures = []

            if busFilter['mode'] == "exclude":
                for bus in busStop['estimatedCalls']:
                    if bus['serviceJourney']['journeyPattern']['line']['publicCode'] not in filterValues:
                        departures.append(bus)

            elif busFilter['mode'] == "include":
                for bus in busStop['estimatedCalls']:
                    if len(filterValues) == 0:
                        departures.append(bus)

                    if bus['serviceJourney']['journeyPattern']['line']['publicCode'] in filterValues:
                        departures.append(bus)
            else:
                raise Exception("filter mode not recognized")

            singleBusStop = None
            for bus in departures:
                busStopName = busStop['estimatedCalls'][0]['quay']['name']
                busStopNumber = busStop['estimatedCalls'][0]['quay']['publicCode']

                if busStopNumber is not None:
                    stopName = busStopName + " " + busStopNumber if busStopNumber is not None else busStopName
                else:
                    stopName = busStopName

                line = bus['serviceJourney']['journeyPattern']['line']['publicCode']
                dest = bus['destinationDisplay']['frontText']
                if len(bus['destinationDisplay']['via']) > 0:
                    via = "via" + bus['destinationDisplay']['via'][0]
                arrival = bus['aimedArrivalTime']
                excpectedArrival = bus['expectedArrivalTime']

                via = None
                excpectedArrivalMinutes = None

                # Format the arrival date to either be "minutes until the bus arrives" 
                # or "HH:MM formatted timestamp for when it arrives"
                excpectedArrivalMinutes =  BusStopInformationService.FormatBusArrivalDate(excpectedArrival)

                # Add "Via" field to the destination
                if via is not None:
                    dest += " via " + via

                # A single bus
                busInstance = BusEntry(
                    line=line,
                    destination=dest,
                    estArrival=datetime.fromisoformat(arrival),
                    hereIn=excpectedArrivalMinutes,
                    busStopName=stopName
                    )
                
                if singleBusStop is not None:
                    singleBusStop.BusEntries.append(busInstance)
                else:
                    # We only go in here the first time, to create the bus stop instance.
                    singleBusStop = BusStops(quayId,stopName)
                    singleBusStop.BusEntries.append(busInstance)

            # When all bus departures have been processed, add them to the list of bus stops
            if singleBusStop is not None:
                busDeparturesFinal.append(singleBusStop)
        busDeparturesFinal = BusStopInformationService.NormalizeToMaxResults(busDeparturesFinal,configuration['maxResultsToView'])
        return busDeparturesFinal

    def FormatBusArrivalDate(arrivalDate):
        excpctArrival_datetime = datetime.fromisoformat(arrivalDate)
        curDate_datetime = datetime.now(timezone.utc)

        time_diff = excpctArrival_datetime - curDate_datetime
        minutes_left = int(time_diff.total_seconds() // 60)
        if minutes_left < 15:
            if minutes_left <= 0:
                return "Nå"
            else:
                return f"{minutes_left} Min"
        else:
            return excpctArrival_datetime.strftime("%H:%M")

    def NormalizeToMaxResults(busDeparturesObject, maxResults):
        for busStop in busDeparturesObject:
            busStop.BusEntries = busStop.BusEntries[:int(maxResults)]
        return busDeparturesObject

    def truncate_array(arr, target_length):
        return arr[:target_length]


def GetStopPlaceByName(busStopsObject,busStopNames):
    busStopQuays = []
    busStopNames = [busStop.lower() for busStop in busStopNames]
    for busQuay in busStopsObject:
        quayName = ReplaceUnknownCharacters(busQuay['name']).lower()

        # Check if its empty string or None (Falsy)
        quayNameWithNumber = ""
        if busQuay['publicCode']:
            quayNameWithNumber =  quayName + " " + busQuay['publicCode']
        
        if quayName in busStopNames or quayNameWithNumber in busStopNames:
            matchingQuay = {
                "id": busQuay['id'],
                "name": ReplaceUnknownCharacters(busQuay['name']),
                "publicCode": busQuay['publicCode'],
                "description": busQuay['description'],
            }
            busStopQuays.append(matchingQuay)
        
    return busStopQuays        

def ReplaceUnknownCharacters(input):
    return input.replace("Ã¸", "ø").replace("Ã¥", "å").replace("Ã¦", "æ").replace("Ã", "Å").replace("Ã†", "Æ").replace("Ã˜", "Ø")  

def update_cache():
    global timetable_cache
    while True:
        try:
            busStopInformationService = BusStopInformationService()
            timetable_cache = busStopInformationService.GetBusStopInformation()
            print("Cache updated")
        except Exception as e:
            print(f"Error updating cache: {e}")
        time.sleep(10)  # Update every 10 seconds


def main():
    app = Flask(__name__)

    # Start the cache updater in a background thread
    updater_thread = Thread(target=update_cache, daemon=True)
    updater_thread.start()

    # Create and run the Flask app

    @app.route('/api/timetable', methods=['GET'])
    def get_timetable():
        return jsonify([bus_stop.to_dict() for bus_stop in timetable_cache])


        # Main route to render the page
    @app.route('/')
    def index():
        return render_template('timetable.html')
    
    app.run(debug=True)

if __name__ == '__main__':
    main()
 