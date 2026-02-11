import re
import requests
import json
import time
from datetime import datetime, timedelta, timezone

from src.helpers.helpers import GetStopPlaceByNameAndFilter, ReplaceUnknownCharacters, NormalizeStopName
from src.models import bus_entry, bus_stops

class BusStopInformationService:

    def __init__(self):
        config = ''.join(open("config.json","r").readlines())
        self.jsonConfig = json.loads(config)
        with open("output.json", "r") as input:  # Using 'a' mode for appending
            content = ''.join(input.readlines())
            quayArray = json.loads(content)
            self.busStops = quayArray
        pass

    def GetBusStopInformation(self, config):
        current_datetime = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
        configuration = config
        headers = self.jsonConfig['clientName']

        configBusStops = [ReplaceUnknownCharacters(busstop) for busstop in configuration['busStops']]

        print(f"Finding bus stops near {', '.join(configBusStops)}..")
        
        busStopQuays = GetStopPlaceByNameAndFilter(self.busStops, configBusStops)

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
        response = requests.post(self.jsonConfig['baseUrl'], json=data, headers=headers)
        
        print(f'Status Code: {response.status_code}')
        
        if response.status_code != 200: 
            raise Exception("HTTP request did not result in 200 OK")
        
        content = response.json()
        
        busDeparturesFinal = []
        
        busStops = content['data']['quays']
        for busStop in busStops:
                        
            busStopItem = busStop.get('estimatedCalls',[])
            
            if len(busStopItem) < 1:
                continue
            
            busStopItem = busStopItem[0]
            
            busFilter = configuration['busFilter']
            
            filterValues = configuration['busFilter']['values']

            departures = []
   
            for bus in busStop['estimatedCalls']:
                busAppendage = None
                
                lineCode = bus['serviceJourney']['journeyPattern']['line']['publicCode']
                
                if busFilter['mode'] == "exclude":
                    if lineCode not in filterValues:
                        busAppendage = bus
                    
                else:
                    if len(filterValues) == 0:
                        busAppendage = bus
                    if lineCode in filterValues:
                        busAppendage = bus
                        
                if busAppendage != None:
                    departures.append(busAppendage)

            busStop = self.NormalizeStopNameDepartures(departures)

            # When all bus departures have been processed, add them to the list of bus stops
            if busStop is not None:
                busDeparturesFinal.append(busStop)

        busDeparturesFinal = BusStopInformationService.NormalizeStopNameToMaxResults(busDeparturesFinal,configuration['maxResultsToView'])
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
        

    def NormalizeStopNameDepartures(self, departures):
        if departures == [] :return
        
        busStop = None
        quayId = departures[0]['quay']['id']
        busStopName = departures[0]['quay']['name']
        busStopNumber = departures[0]['quay']['publicCode']
        busStopDescription = departures[0]['quay']['description'] or ""

        for bus in departures:
            if busStopNumber is not None:
                stopName = busStopName + " " + busStopNumber if busStopNumber is not None else busStopName
            else:
                stopName = busStopName

            line = bus['serviceJourney']['journeyPattern']['line']['publicCode']
            dest = bus['destinationDisplay']['frontText']
            
            if (vias := bus['destinationDisplay'].get('via')):
                via = "via " + vias[0]
                
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
            busInstance = bus_entry.BusEntry(
                line=line,
                destination=dest,
                estArrival=datetime.fromisoformat(arrival),
                hereIn=excpectedArrivalMinutes,
                stopName=stopName
                )
            
            if busStop is not None:
                busStop.BusEntries.append(busInstance)
            else:
                # We only go in here the first time, to create the bus stop instance.
                busStop = bus_stops.BusStops(quayId,stopName,busStopDescription)
                busStop.BusEntries.append(busInstance)
                
        return busStop

    def NormalizeStopNameToMaxResults(busDeparturesObject, maxResults):
        for busStop in busDeparturesObject:
            busStop.BusEntries = busStop.BusEntries[:int(maxResults)]
        return busDeparturesObject

    def truncate_array(arr, target_length):
        return arr[:target_length]

