from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from requests.auth import HTTPBasicAuth
import os

app = Flask(__name__)
CORS(app)  # Allow all origins (frontend can call this)

RACING_API_BASE = "https://api.theracingapi.com/v1"


def racing_get(path, username, password, params=None):
    """Make authenticated request to Racing API."""
    url = f"{RACING_API_BASE}{path}"
    resp = requests.get(
        url,
        auth=HTTPBasicAuth(username, password),
        params=params or {},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/horse", methods=["POST"])
def get_horse():
    """Get horse data: search + results + stats."""
    data = request.json
    name = data.get("name")
    username = data.get("username")
    password = data.get("password")

    if not all([name, username, password]):
        return jsonify({"error": "Missing name/username/password"}), 400

    try:
        # Search horse
        search = racing_get("/horses", username, password, {"search": name, "limit": 1})
        horses = search.get("horses") or search if isinstance(search, list) else []
        if not horses:
            return jsonify({"found": False, "name": name})

        horse = horses[0]
        horse_id = horse.get("id") or horse.get("horse_id")

        result = {
            "found": True,
            "name": horse.get("name", name),
            "age": horse.get("age"),
            "trainer": horse.get("trainer"),
            "owner": horse.get("owner"),
        }

        # Get results
        try:
            results_data = racing_get(f"/horses/{horse_id}/results", username, password, {"limit": 10})
            results = results_data.get("results", [])
            result["results"] = [
                {
                    "date": r.get("date"),
                    "course": r.get("course"),
                    "distance": r.get("distance"),
                    "going": r.get("going"),
                    "position": r.get("position"),
                    "runners": r.get("runners"),
                    "class": r.get("class"),
                    "odds": r.get("sp"),
                }
                for r in results[:10]
            ]
        except Exception as e:
            result["results"] = []
            result["results_error"] = str(e)

        # Get stats
        try:
            stats = racing_get(f"/horses/{horse_id}/stats", username, password)
            result["stats"] = stats
        except Exception as e:
            result["stats"] = None
            result["stats_error"] = str(e)

        return jsonify(result)

    except requests.exceptions.HTTPError as e:
        return jsonify({"error": f"Racing API error: {e.response.status_code}", "found": False}), 200
    except Exception as e:
        return jsonify({"error": str(e), "found": False}), 200


@app.route("/horses-batch", methods=["POST"])
def get_horses_batch():
    """Get data for multiple horses at once."""
    data = request.json
    names = data.get("names", [])
    username = data.get("username")
    password = data.get("password")

    if not all([names, username, password]):
        return jsonify({"error": "Missing names/username/password"}), 400

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
            }

            try:
                r = racing_get(f"/horses/{horse_id}/results", username, password, {"limit": 8})
                entry["results"] = r.get("results", [])[:8]
            except:
                entry["results"] = []

            try:
                entry["stats"] = racing_get(f"/horses/{horse_id}/stats", username, password)
            except:
                entry["stats"] = None

            results[name] = entry

        except Exception as e:
            results[name] = {"found": False, "error": str(e)}

    return jsonify(results)


@app.route("/racecards/today", methods=["POST"])
def get_today_racecards():
    """Get today's racecards for UK/Ireland."""
    data = request.json
    username = data.get("username")
    password = data.get("password")
    region = data.get("region", "gb")  # gb or ire

    try:
        cards = racing_get("/racecards/standard", username, password, {"region": region})
        return jsonify(cards)
    except Exception as e:
        return jsonify({"error": str(e)}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
