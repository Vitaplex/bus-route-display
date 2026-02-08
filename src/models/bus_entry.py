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