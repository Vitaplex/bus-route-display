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