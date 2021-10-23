from flask import Flask, request, jsonify, render_template, abort
from pyppeteer import launch

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
    try:
        departureList = []
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
                    if _AIRLINE.lower().replace(" ", "") != filterAirline.lower().replace(" ", ""):
                        continue
                if filterDestination:
                    if _DEST.lower().replace(" ", "") != filterDestination.lower().replace(" ", ""):
                        continue

                entry = {
                    _DATE + ", " + _TIME: {
                        "Airline": _AIRLINE,
                        "Destination": _DEST,
                        "Flight Number": _FLIGHTNO
                    }}
                departureList.append(entry)
        return departureList
    except ValueError:
        abort(500)


async def generateDeparturesJSON(filterAirline=None, filterDestination=None):
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
    await browser.close()
    return departureDict


def inputIsValid(query):
    if query:
        if len(query.replace(" ", "")) != 0:
            return True
    return False


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/departures")
async def departures():
    try:
        d = await generateDeparturesJSON()
        return jsonify(d)
    except ValueError:
        abort(500)


@app.route("/departures/search", methods=["GET"])
async def search():
    # Gather optional arguments in search query
    airline = request.args.get("airline", None)
    airline = airline if inputIsValid(airline) else None
    destination = request.args.get("destination", None)
    destination = destination if inputIsValid(destination) else None
    try:
        d = await generateDeparturesJSON(filterAirline=airline, filterDestination=destination)
        # Calls jsonify automatically if Flask version > 1.1.0
        return jsonify(d)
    except ValueError:
        abort(404)


if __name__ == "__main__":
    print("Starting server...")
    app.run(debug=True)

