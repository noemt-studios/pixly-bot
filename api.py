from quart import Quart, request, jsonify, render_template
from quart_cors import cors
from pymongo import MongoClient

app = Quart(__name__)
app = cors(app, allow_origin="*")

db = MongoClient("mongodb://127.0.0.1:27017/")["pixly"]
discord_links = db["users"]
profiles = db["profiles"]

def parse_data(data: dict):
    parsed = {}
    for _ in data:
        if _ == "_id":
            continue

        parsed[_] = data[_]

    return parsed

@app.route("/docs", methods=["GET"])
async def docs():
    return await render_template("documentation.html")

@app.route("/user-data/<discord_id>", methods=["GET"])
async def user_data(discord_id: str):
    if not discord_id.isdigit():
        return {"status": "error", "message": "Invalid Discord ID provided"}
    
    discord_id = int(discord_id)
    user_data = discord_links.find_one({"discord": discord_id})

    if user_data is None:
        return {"status": "error", "message": "User not found"} 
    

    return {"status": "success", "data": parse_data(user_data)}

@app.route('/get-cached-players-count')
async def get_cached_players_count():
    count = profiles.count_documents({})
    return {"status": "success", "count": count}