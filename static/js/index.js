const QUAYMAP = await(await fetch("/static/data/quays.json")).json()
const BASEURL = "https://api.entur.io/journey-planner/v3/graphql";

const ACTIVESTOPS = new Set();
const ACTIVEQUAYS = new Set();

updateTimeTable();

setInterval(updateTimeTable, 5000);


async function updateTimeTable() {

    let searchConfig = JSON.parse(GetCookie("config"))

    let graphQlQuery = getGraphQlQueryFromConfig(searchConfig);

    let response = await fetch(BASEURL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(graphQlQuery)
    })

    var content = await response.json();
    var formattedContent = formatContent(content);

    presentContent(formattedContent, searchConfig);
}

function formatContent(content) {
    var stops = [];
    for (let i = 0; i < content.data.quays.length; i++) {
        const busStop = content.data.quays[i];

        const calls = busStop.estimatedCalls;
        const firstCall = calls[0];
        if (!firstCall) continue;
        const quay = calls[0].quay;

        let object = {
            "name": quay.name,
            "description": quay.description,
            "id": quay.id,
            "arrivals": calls
        };
        stops.push(object);
    }

    return stops;
}

function presentContent(busStops, config) {
    const busStopContainer = document.querySelector('#busStopsContainer');

    const processedQuays = new Set();

    for (let i = 0; i < busStops.length; i++) {
        const quay = busStops[i];

        const quayId = quay.id.replace(/:/g, "_");

        // Try to get existing element
        let busStopElement = document.getElementById(quayId);

        if (!busStopElement) {
            const wrapper = document.createElement("div");
            wrapper.className = "table-wrapper";
            wrapper.id = quayId + "_wrapper";

            busStopElement = document.createElement("table");
            busStopElement.id = quayId;

            const headerRow = document.createElement('tr');
            const headerCell = createHeaderCell(quay);
            headerRow.appendChild(headerCell);
            busStopElement.appendChild(headerRow);

            // Add a sub-header row for column names
            const subHeaderRow = document.createElement('tr');
            subHeaderRow.innerHTML = `
                        <th>Linje</th>
                        <th class="middleRow"></th>
                        <th>Ankomst</th>
            `;
            
            
            wrapper.appendChild(busStopElement);
            
            busStopElement.appendChild(subHeaderRow);
            busStopContainer.appendChild(wrapper);
            autoScroll(wrapper);
        }

        processedQuays.add(quayId);
        ACTIVEQUAYS.add(quayId);

        const processedArrivals = new Set();

        for (let j = 0; j <= config.maxResultsToView; j++) {

            const arrival = quay.arrivals[j];
            if (!arrival) continue;

            const arrivalId = quayId + "_" + j;
            let arrivalRow = document.getElementById(arrivalId);

            if (!arrivalRow) {
                arrivalRow = document.createElement("tr");
                arrivalRow.id = arrivalId;

                busStopElement.appendChild(arrivalRow);
            }

            let arrivalTime = getFormattedTimeFromArrivalTime(arrival.expectedArrivalTime);

            arrivalRow.innerHTML = `
                <td id="busLine"><svg xmlns="http://www.w3.org/2000/svg" width="20" viewBox="0 0 576 512"><!-- c u r s e d --><path d="M288 0C422.4 0 512 35.2 512 80l0 16 0 32c17.7 0 32 14.3 32 32l0 64c0 17.7-14.3 32-32 32l0 160c0 17.7-14.3 32-32 32l0 32c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-32-192 0 0 32c0 17.7-14.3 32-32 32l-32 0c-17.7 0-32-14.3-32-32l0-32c-17.7 0-32-14.3-32-32l0-160c-17.7 0-32-14.3-32-32l0-64c0-17.7 14.3-32 32-32c0 0 0 0 0 0l0-32s0 0 0 0l0-16C64 35.2 153.6 0 288 0zM128 160l0 96c0 17.7 14.3 32 32 32l112 0 0-160-112 0c-17.7 0-32 14.3-32 32zM304 288l112 0c17.7 0 32-14.3 32-32l0-96c0-17.7-14.3-32-32-32l-112 0 0 160zM144 400a32 32 0 1 0 0-64 32 32 0 1 0 0 64zm288 0a32 32 0 1 0 0-64 32 32 0 1 0 0 64zM384 80c0-8.8-7.2-16-16-16L208 64c-8.8 0-16 7.2-16 16s7.2 16 16 16l160 0c8.8 0 16-7.2 16-16z"/></svg>
                    ${arrival.serviceJourney.journeyPattern.line.publicCode}
                </td>
                <td class="middleRow">${arrival.destinationDisplay.frontText}</td>
                <td>${arrivalTime}</td>
            `;

            processedArrivals.add(arrivalId);
            ACTIVESTOPS.add(arrivalId);
        }

        let arrivalString = [...ACTIVESTOPS].filter(id => id.startsWith(quayId + "_")).filter(pa => !processedArrivals.has(pa)).map(id => { ACTIVESTOPS.delete(id); return `[id='${id}']`; }).join(', ');


        if (arrivalString) {
            console.log("Deleting arrivals: " + arrivalString);
            document.querySelectorAll(arrivalString).forEach(itm => itm.remove());
        }

        processedArrivals.clear();
    }

    let quayString = [...ACTIVEQUAYS].filter(pa => !processedQuays.has(pa)).map(id => { ACTIVEQUAYS.delete(id); return `[id='${id}']`; }).join(', ');

    if (quayString) {
        console.log("Deleting stations: " + quayString);
        document.querySelectorAll(quayString).forEach(itm => itm.remove());
    }

    // Remove empty table wrapper containers
    document.querySelectorAll('[id$=_wrapper]:empty').forEach(wrp => wrp.remove());

    processedQuays.clear();
    
    const tables = document.querySelectorAll("table");
    fixStickyHeaders(tables);
}

function autoScroll(element) {
    const speed = 0.5;
    const pauseAtBottom = 4000;
    const pauseAtTop = 4000;

    let paused = false;
    let waiting = false;
    let scrollPosition = 0;

    element.addEventListener("mouseenter", () => paused = true);
    element.addEventListener("mouseleave", () => paused = false);

    function step() {
        const maxScroll = element.scrollHeight - element.clientHeight;

        if (!paused && !waiting && maxScroll > 0) {
            scrollPosition += speed;
            element.scrollTop = scrollPosition;

            if (scrollPosition >= maxScroll) {
                waiting = true;

                setTimeout(() => {
                    scrollPosition = 0;
                    element.scrollTop = 0;

                    setTimeout(() => {
                        waiting = false;
                    }, pauseAtTop);

                }, pauseAtBottom);
            }
        }

        requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
}
function fixStickyHeaders(tables){
    if(!tables) return;

    for(const table of tables){
        freezeTopRows(table,12);

        window.addEventListener("resize", () => {
            freezeTopRows(table, 12);
        });
    }

}

function freezeTopRows(table, n) {
    const rows = table.querySelectorAll("tr");

    let offset = 0;
    const loopNumber = Math.min(n, rows.length);

    for (let i = 0; i < loopNumber; i++) {
        const row = rows[i];

        row.style.position = "sticky";
        row.style.top = `${offset - 1}px`;

        offset += Math.round(row.offsetHeight);
        
        if(i === loopNumber-1){
            row.style.boxShadow = "5px 5px 10px rgba(0,0,0,0.5)";
        }
    }
}

function createHeaderCell(quay) {
    const headerCell = document.createElement('th');
    headerCell.colSpan = 3;
    headerCell.innerHTML = `${quay.name}<br>&nbsp;`;
    if (quay.description) {
        headerCell.innerHTML += `<sup>${quay.description}</sup>`;
    }

    headerCell.addEventListener("mouseenter", () => {
	headerCell.innerHTML = `${quay.id}<br>&nbsp;`;
    });

    headerCell.addEventListener("mouseleave", () => {
	headerCell.innerHTML = `${quay.name}<br>&nbsp;`;
    });

    headerCell.style.textAlign = 'center';

    return headerCell;
}

function getFormattedTimeFromArrivalTime(dateTime) {
    let instance = new Date(dateTime);
    let now = new Date();

    let deltaMinutes = (instance.getTime() - now.getTime()) / (1000 * 60);
    let delta = Math.round(Math.abs(deltaMinutes));

    if (delta == 0) {
        return "<span id='now'>Nå</span>";
    }

    let minutes = new String(instance.getMinutes()).padStart(2, "0");
    let hours = new String(instance.getHours()).padStart(2, "0");

    
    
    if (delta > 15) {
        return `<span id='time'>${hours}:${minutes}</span>`;
    }
    
    if (delta < 5) {
        return `<span id='soon'>${delta} Min</span>`;
    }

    return `<span id='minutes'>${delta} Min</span>`;
}

function getGraphQlQueryFromConfig(config) {
    var stopQuays = getStopIdsFromNameSearch(config.busStops);

    return {
        "operationName": "getDeparturesForQuays",
        "variables": {
            "ids": stopQuays.map(sq => sq.id),
            "arrivalDeparture": "departures",
            "numberOfDepartures": config.maxResultsToGet,
            "travelDate": new Date().toISOString()
        },
        "query": "query getDeparturesForQuays($ids: [String!]!, $numberOfDepartures: Int, $arrivalDeparture: ArrivalDeparture, $travelDate: DateTime, $lines: [ID]) {\n  quays(ids: $ids) {\n    id\n    estimatedCalls(\n      arrivalDeparture: $arrivalDeparture\n      includeCancelledTrips: true\n      numberOfDepartures: $numberOfDepartures\n      startTime: $travelDate\n      whiteListed: {lines: $lines}\n    ) {\n      date\n      aimedArrivalTime\n      aimedDepartureTime\n      bookingArrangements {\n        latestBookingTime\n        latestBookingDay\n        minimumBookingPeriod\n        bookingNote\n        bookWhen\n        bookingContact {\n          contactPerson\n          email\n          url\n          phone\n          furtherDetails\n          __typename\n        }\n        __typename\n      }\n      serviceJourney {\n        id\n        journeyPattern {\n          line {\n            id\n            publicCode\n            __typename\n          }\n          __typename\n        }\n        notices {\n          id\n          text\n          __typename\n        }\n        transportMode\n        transportSubmode\n        __typename\n      }\n      cancellation\n      expectedArrivalTime\n      expectedDepartureTime\n      destinationDisplay {\n        frontText\n        via\n        __typename\n      }\n      notices {\n        id\n        text\n        __typename\n      }\n      predictionInaccurate\n      quay {\n        id\n        name\n        description\n        publicCode\n        stopPlace {\n          name\n          description\n          __typename\n        }\n        __typename\n      }\n      realtime\n      situations {\n        situationNumber\n        summary {\n          value\n          language\n          __typename\n        }\n        description {\n          value\n          language\n          __typename\n        }\n        advice {\n          value\n          language\n          __typename\n        }\n        validityPeriod {\n          startTime\n          endTime\n          __typename\n        }\n        reportType\n        infoLinks {\n          uri\n          label\n          __typename\n        }\n        __typename\n      }\n      occupancyStatus\n      __typename\n    }\n    __typename\n  }\n}"
    }
}

function getStopIdsFromNameSearch(stopNames) {
    let ids = [];

    for (let i = 0; i < stopNames.length; i++) {
        const [element, description] = stopNames[i].split("||");
        
        let quayIds = QUAYMAP.filter(qy => qy.name.match(new RegExp(element, "gi")) || qy.id === element);

	console.log(quayIds);

	if(description){
            quayIds = quayIds.filter(qy => qy.description != null && qy.description.match(new RegExp(description, "gi")))
        }

        quayIds.forEach(id => {
            ids.push(id);
        });
    }
    return ids;
}
