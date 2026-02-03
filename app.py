from flask import Flask, request, Response
from birthchart_module import generate_csv_from_params

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "RB Astro App is running! Use /download with query parameters."

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for uptime monitoring"""
    return {"status": "ok"}, 200

@app.route("/download", methods=["GET"])
def download_csv():
    try:
        # Grab query params safely
        utc_offset = request.args.get("utcoffset")
        longitude = request.args.get("long")
        latitude = request.args.get("lat")

        # Check required params
        if not all([utc_offset, longitude, latitude]):
            return {"error": "Missing one of: utcoffset, long, lat"}, 400

        params = {
            "name": request.args.get("name", "Unknown"),
            "dob": request.args.get("dob"),
            "tob": request.args.get("tob"),
            "utc_offset": float(utc_offset),
            "longitude": float(longitude),
            "latitude": float(latitude),
        }

        # Generate CSV from your custom module
        #MAIN CODE CALLED FROM THE LINE BELOW! YAY:):) --->
        csv_bytes = generate_csv_from_params(params)

        # Send CSV as downloadable file
        return Response(
            csv_bytes,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment;filename=astro.csv"}
        )

    except Exception as e:
        return {"error": str(e)}, 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
