import re

def GetStopPlaceByNameAndFilter(busStopsObject, configBusStops):
    busStopQuays = []

    parsedFilters = GetStopFiltersFromBusStops(configBusStops)
    busStopNames = NormalizeStopName(configBusStops)
    compiledRegexPatternStopNames = [re.compile(pattern, re.I) for pattern in busStopNames]

    for busQuay in busStopsObject:
        quayName = ReplaceUnknownCharacters(busQuay['name']).lower()
        quayDescription = str(busQuay.get('description') or "")
        quayPublicCode = busQuay.get('publicCode')

        quayNameWithNumber = f"{quayName} {quayPublicCode}" if quayPublicCode else quayName

        if not any(p.match(quayName) or p.match(quayNameWithNumber) for p in compiledRegexPatternStopNames):
            continue

        matchingFilter = None

        for pattern in parsedFilters:
            
            namePattern = pattern.get('stop_pattern')
            descPattern = pattern.get('stop_description')
            
            nameMatch = re.search(namePattern, quayName) or re.match(pattern.get('stop_pattern', ''), quayNameWithNumber)
            
            descMatch = re.search(descPattern, quayDescription) if descPattern is not None else None

            if (nameMatch and not descPattern) or descMatch:
                matchingFilter = pattern
                break

        if not matchingFilter:
            continue

        matchingQuay = {
            "id": busQuay['id'],
            "name": ReplaceUnknownCharacters(busQuay['name']),
            "publicCode": quayPublicCode,
            "description": quayDescription,
            "filter": matchingFilter
        }

        busStopQuays.append(matchingQuay)

    return busStopQuays
    
def NormalizeStopName(inputList):
    newlist = []
    for input in inputList:
        input = input.lower()
        inputParts = input.split("||")
        if len(inputParts) > 1:
            input = inputParts[0]
        newlist.append(input)
    return newlist

def ReplaceUnknownCharacters(input):
    return input.replace("Ã¸", "ø").replace("Ã¥", "å").replace("Ã¦", "æ").replace("Ã", "Å").replace("Ã†", "Æ").replace("Ã˜", "Ø")  


def GetStopFiltersFromBusStops(busStops):
    parsedFilters = []

    for stop in busStops:
        parts = stop.split("||")

        stop_pattern = parts[0].strip()
        description_pattern = None
        
        if len(parts)>1:
            description_pattern = parts[1].strip()

        parsedFilters.append({
            "stop_pattern": re.compile(stop_pattern, re.IGNORECASE),
            "stop_description": re.compile(description_pattern, re.IGNORECASE) if description_pattern is not None else None
        })
        
    return parsedFilters
