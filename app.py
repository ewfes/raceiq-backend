import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from requests.auth import HTTPBasicAuth
import anthropic

app = Flask(__name__)
CORS(app)

RACING_API_BASE = "https://api.theracingapi.com/v1"


def get_claude():
    return anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def racing_get(path, username, password, params=None):
    url = f"{RACING_API_BASE}{path}"
    resp = requests.get(url, auth=HTTPBasicAuth(username, password), params=params or {}, timeout=15)
    resp.raise_for_status()
    return resp.json()


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/analyse", methods=["POST"])
def analyse():
    """Extract horses from screenshot using Claude Vision."""
    data = request.get_json(force=True) or {}
    image_b64 = data.get("image")
    if not image_b64:
        return jsonify({"error": "No image provided"}), 400
    try:
        client = get_claude()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}},
                {"type": "text", "text": 'Racing racecard image. Return ONLY raw JSON (no markdown): {"race":{"venue":"str","time":"str","distance":"str","going":"str"},"horses":[{"name":"str","number":"str","odds":"str","jockey":"str","trainer":"str"}]} Use null for unknown. List every horse.'}
            ]}]
        )
        return jsonify({"result": msg.content[0].text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/analyse-horses", methods=["POST"])
def analyse_horses():
    """Analyse horses and return predictions."""
    data = request.get_json(force=True) or {}
    horses_list = data.get("horses_list", "")
    race_info = data.get("race_info", "")
    try:
        client = get_claude()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": f"""Horse racing expert. Race: {race_info}

{horses_list}

Return ONLY raw JSON (no markdown):
{{"horses":[{{"name":"exact name","score":50,"reasoning":"Ukrainian max 25 words","isValue":false}}],"topPick":"name","valueBet":"name or null","summary":"Ukrainian max 35 words"}}

score=win probability 0-100. isValue=true if odds much higher than probability. Include ALL horses."""}]
        )
        return jsonify({"result": msg.content[0].text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/horses-batch", methods=["POST"])
def get_horses_batch():
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
            entry = {"found": True, "name": horse.get("name", name), "results": [], "stats": None}
            try:
                r = racing_get(f"/horses/{horse_id}/results", username, password, {"limit": 8})
                entry["results"] = r.get("results", [])[:8]
            except:
                pass
            results[name] = entry
        except Exception as e:
            results[name] = {"found": False, "error": str(e)}
    return jsonify(results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False, threaded=True)
