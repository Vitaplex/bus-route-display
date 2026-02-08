import requests, json
import time
headers = { "ET-Client-Name":"NTNU-IT_OYA_UTVIKLING" }

quayID = 99999
quayList = []
entriesPerHttpRequest = 150
while quayID < 150000:
    originalQuayId = quayID
    dbg = originalQuayId + entriesPerHttpRequest
    busStops = []
    while quayID < dbg:
        busStops.append(f"NSR:Quay:{quayID}")
        quayID += 1
    busstopsString = str(busStops).replace("'",'"')
    query = f"""
    {{
    quays(ids: {busstopsString}) {{
        id
        name
        publicCode
        description
    }}
    }}
    """
    data =  {
                "query":query
            }
    response = requests.post("https://api.entur.io/journey-planner/v3/graphql", json=data, headers=headers)
    content = response.json()
    filteredQuays = [bit for bit in content['data']['quays'] if bit is not None]
    quayList += filteredQuays
    print(f"found {len(filteredQuays)} results. total is now {len(quayList)}" )
    if len(filteredQuays) == 0:
        break
    time.sleep(0.25)

with open("output.json", "a") as output:  # Using 'a' mode for appending
    json.dump(quayList, output)  # Writes the entire JSON object
    output.write("\n")  # Add a newline after each entry for better readability
pass
