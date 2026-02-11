class BusEntry:
    def __init__(self,line,destination,estArrival,hereIn,stopName):
        self.busStopName = stopName 
        self.line = line
        self.destination = destination
        self.estArrival = estArrival 
        self.hereIn = hereIn # in minutes or HH:MM time

    def to_dict(self):
        return {
            'busStopName': self.busStopName,
            'line': self.line,
            'destination': self.destination,
            'estArrival': self.estArrival,
            'hereIn': self.hereIn
        }