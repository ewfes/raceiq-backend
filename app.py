import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
CORS(app)

RACING_API_BASE = "https://api.theracingapi.com/v1"

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/horses-batch", methods=["POST"])
def horses_batch():
    data = request.get_json(force=True) or {}
    names = data.get("names", [])
    username = data.get("username")
    password = data.get("password")
    results = {}
    for name in names:
        try:
            s = requests.get(f"{RACING_API_BASE}/horses", auth=HTTPBasicAuth(username, password), params={"search": name, "limit": 1}, timeout=15).json()
            horses = s.get("horses") or []
            if not horses:
                results[name] = {"found": False}
                continue
            h = horses[0]
            hid = h.get("id")
            entry = {"found": True, "name": h.get("name", name), "results": [], "stats": None}
            try:
                entry["results"] = requests.get(f"{RACING_API_BASE}/horses/{hid}/results", auth=HTTPBasicAuth(username, password), params={"limit": 8}, timeout=15).json().get("results", [])
            except: pass
            results[name] = entry
        except Exception as e:
            results[name] = {"found": False, "error": str(e)}
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)