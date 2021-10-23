from flask import Flask, request, jsonify, render_template, Blueprint
from pyppeteer import launch
from enum import Enum

# init
app = Flask(__name__)
URL = r"https://www.tallinn-airport.ee/en/flight-info/realtime-flights/"


class DepartureData:
    DATETIME = 0
    DESTINATION = 1
    FLIGHTNO = 2
    AIRLINE = 3
    INFORMATION = 4


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


def departureDataToDict(flightData, filterAirline, filterDestination):
    departureList = []
    _DATE = None
    _TIME = None
    _DEST = None
    _FLIGHTNO = None
    _AIRLINE = None
    _INFORMATION = None

    for flight in flightData[1:]:
        if len(flight) == 1:
            # This signifies a row containing the DATE
            _DATE = flight[0]
        else:
            _TIME = flight[DepartureData.DATETIME]
            _DEST = flight[DepartureData.DESTINATION]
            _FLIGHTNO = flight[DepartureData.FLIGHTNO]
            _AIRLINE = flight[DepartureData.AIRLINE]
            _INFORMATION = flight[DepartureData.INFORMATION]
            if filterAirline:
                if _AIRLINE.lower().strip() != filterAirline.lower().strip():
                    continue
            if filterDestination:
                if _DEST.lower().strip() != filterDestination.lower().strip():
                    continue
            entry = {
                _DATE + ", " + _TIME: {
                    "Airline": _AIRLINE,
                    "Destination": _DEST,
                    "Flight Number": _FLIGHTNO
                }}
            departureList.append(entry)
    return departureList


async def generateDeparturesJSON(filterAirline='', filterDestination=''):
    # Create browser instance and navigate to website
    browser = await launch(
        handleSIGINT=False,
        handleSIGTERM=False,
        handleSIGHUP=False
    )
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
    cleaned = cleanData(data)
    departureDict = departureDataToDict(cleaned, filterAirline, filterDestination)
    return departureDict


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/departures")
async def departures():
    try:
        d = await generateDeparturesJSON()
        return jsonify(d)
    except TimeoutError:
        return 408


# @app.route("/departures/search")
# async def search():
#     # Gather optional arguments in search query
#     airline = request.args.get("airline", None)
#     destination = request.args.get("destination", None)
#     try:
#         d = await generateDeparturesJSON(filterAirline=airline, filterDestination=destination)
#         # Calls jsonify automatically if Flask version > 1.1.0
#         return jsonify(d)
#     except TimeoutError:
#         return 408


def inputIsValid(searchQuery):
    if searchQuery:
        if len(searchQuery.strip()) != 0:
            return True
    return False


@app.route("/departures/search", methods=["GET", "POST"])
async def search():
    # Gather optional arguments in search query
    airline = request.values.get("airline")
    airline = airline if inputIsValid(airline) else ''
    destination = request.values.get("destination")
    destination = destination if inputIsValid(destination) else ''

    try:
        d = await generateDeparturesJSON(filterAirline=airline, filterDestination=destination)
        # Calls jsonify automatically if Flask version > 1.1.0
        return jsonify(d)
        #return destination
    except TimeoutError:
        return 408


if __name__ == "__main__":
    print("Starting server...")
    app.run(debug=True)

