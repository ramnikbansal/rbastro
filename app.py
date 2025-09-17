from flask import Flask, request, send_file, Response
import io
from birthchart_module import generate_csv_from_params

app = Flask(__name__)

@app.route("/download", methods=["GET"])
def download_csv():
    try:
        # Read parameters from query string
        params = {
            "name": request.args.get("name"),
            "dob": request.args.get("dob"),
            "tob": request.args.get("tob"),
            "utc_offset": float(request.args.get("utcoffset")),
            "longitude": float(request.args.get("long")),
            "latitude": float(request.args.get("lat")),
        }

        # Generate CSV
        csv_bytes = generate_csv_from_params(params)

        # Send CSV as download
        return Response(
            csv_bytes,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=astro.csv"}
        )

    except Exception as e:
        return {"error": str(e)}, 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
