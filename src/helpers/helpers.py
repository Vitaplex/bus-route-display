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
