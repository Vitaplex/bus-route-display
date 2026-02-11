class BusStops:
    def __init__(self,quayId,stopName, stopDescription):
        self.quayId = quayId
        self.stopName = stopName
        self.busStopDescription = stopDescription 

        self.BusEntries = []

    def to_dict(self):
        # Convert the BusStops object into a dictionary
        return {
            'quayId': self.quayId,
            'stopName': self.stopName,
            'busStopDescription': self.busStopDescription,
            'BusEntries': [entry.to_dict() for entry in self.BusEntries]  # Convert each BusEntry object in BusEntries list to dictionary
        }