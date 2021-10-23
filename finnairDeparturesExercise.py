from pyppeteer import launch
import asyncio
import json


def departureDataToDict(flightData, filterAirline=None):
    departureList = []
    _DATE = None
    _TIME = None
    _DEST = None
    _FLIGHTNO = None
    _AIRLINE = None
    _INFORMATION = None

    for flight in flightData[1:]:
        if len(flight) < len(flightData[0]):
            _DATE = flight[0]
        else:
            _TIME = flight[0]
            _DEST = flight[1]
            _FLIGHTNO = flight[2]
            _AIRLINE = flight[3]
            _INFORMATION = flight[4]

            if filterAirline:
                if _AIRLINE.lower().strip() != filterAirline.lower().strip():
                    continue
            entry = {
                _DATE + ", " + _TIME: {
                    "Airline": _AIRLINE,
                    "Destination": _DEST,
                    "Flight Number": _FLIGHTNO
                }}
            departureList.append(entry)
    return departureList


def cleanData(data):
    # Clean information by removing white space
    flights = []
    for item in data:
        newItem = []
        for subItem in item:
            noSpace = subItem.split()
            newItem.append(' '.join(noSpace))
        flights.append(newItem)
    return flights


def exportJSON(d, output):
    with open(output, 'w') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)


async def main():

    print("Extracting data...")
    # Create a browser instance and go to website
    outputPath = r"finnairDepartures.json"
    URL = r"https://www.tallinn-airport.ee/en/flight-info/realtime-flights/"
    browser = await launch()
    page = await browser.newPage()
    await page.goto(URL)

    # Query for corresponding information
    data = await page.evaluate('''
        () => {
            const departuresTable = document.querySelector('[data-flights-type="departures"]')
            const availableFlights = departuresTable.querySelectorAll('.t-row:not(.hidden)')
            const d = []
            for (var i = 0; i < availableFlights.length; i++) {
                const item = []
                for (var j = 0; j < availableFlights[i].children.length; j++) {
                    item.push(availableFlights[i].children[j].innerText)
                }
                d.push(item)
            }
            return d
        }
    ''')

    # Clean data by removing whitespaces, then convert to dictionary
    cleaned = cleanData(data)
    finnairDict = departureDataToDict(cleaned, "Finnair")

    # Export dictionary as a JSON file
    exportJSON(finnairDict, outputPath)

    await browser.close()
    print("Done.")


if __name__ == "__main__":
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except EOFError:
        print("failed to run")
        exit(1)

