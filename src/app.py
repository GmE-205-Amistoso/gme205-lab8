import json
import psycopg
from flask import Flask, Response, request
from pipeline import ParcelPipeline

app = Flask(__name__)
ALLOWED_USES = {"Residential", "Commercial", "Industrial"}

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "GmE 205 Lab 8"}

@app.get("/parcels")
def parcels():
    land_use = request.args.get("land_use", "Residential")
    
    if land_use not in ALLOWED_USES:
        return {"error": "Unsupported land_use value"}, 400

    try:
        collection = ParcelPipeline(land_use).run()
    except psycopg.OperationalError:
        app.logger.exception("PostGIS connection unavailable.")
        return {"error": "Spatial database unavailable"}, 503
    except (psycopg.Error, ValueError):
        app.logger.exception("Parcel service failed.")
        return {"error": "Could not prepare parcel data"}, 500

    return Response(
        json.dumps(collection),
        mimetype="application/geo+json",
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)