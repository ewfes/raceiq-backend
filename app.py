import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type"], methods=["GET", "POST", "OPTIONS"])

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


import anthropic

@app.route("/analyse", methods=["POST"])
def analyse():
    data = request.get_json(force=True) or {}
    image_b64 = data.get("image")
    horses_list = data.get("horses_list", "")
    race_info = data.get("race_info", "")
    username = data.get("username")
    password = data.get("password")
    
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Extract horses from image
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        messages=[{"role":"user","content":[
            {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":image_b64}},
            {"type":"text","text":'Racing racecard. Return ONLY raw JSON: {"race":{"venue":"str","time":"str","distance":"str","going":"str"},"horses":[{"name":"str","number":"str","odds":"str","jockey":"str","trainer":"str"}]}'}
        ]}]
    )
    return jsonify({"result": msg.content[0].text})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, use_reloader=False, threaded=True)