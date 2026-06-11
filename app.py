import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

RACING_API_BASE = "https://api.theracingapi.com/v1"


def racing_get(path, username, password, params=None):
    url = f"{RACING_API_BASE}{path}"
    resp = requests.get(
        url,
        auth=HTTPBasicAuth(username, password),
        params=params or {},
        timeout=15
    )
    resp.raise_for_status()
    return resp.json()


@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "ok", "service": "RaceIQ Backend v2"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/horses-batch", methods=["POST", "OPTIONS"])
def get_horses_batch():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200

    data = request.get_json(force=True) or {}
    names = data.get("names", [])
    username = data.get("username")
    password = data.get("password")

    if not username or not password or not names:
        return jsonify({"error": "Missing fields"}), 400

    results = {}
    for name in names:
        try:
            search = racing_get("/horses", username, password, {"search": name, "limit": 1})
            horses = search.get("horses") or (search if isinstance(search, list) else [])
            if not horses:
                results[name] = {"found": False}
                continue

            horse = horses[0]
            horse_id = horse.get("id") or horse.get("horse_id")
            entry = {
                "found": True,
                "name": horse.get("name", name),
                "age": horse.get("age"),
                "trainer": horse.get("trainer"),
                "results": [],
                "stats": None,
            }

            try:
                r = racing_get(f"/horses/{horse_id}/results", username, password, {"limit": 8})
                entry["results"] = r.get("results", [])[:8]
            except:
                pass

            try:
                entry["stats"] = racing_get(f"/horses/{horse_id}/stats", username, password)
            except:
                pass

            results[name] = entry

        except Exception as e:
            results[name] = {"found": False, "error": str(e)}

    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
