# app.py - Flask web dashboard with Wikipedia and Wikidata fallback for thumbnails

from flask import Flask, render_template, jsonify, request, send_file, redirect, url_for
import mariadb
import requests
import io
import os
import hashlib
from datetime import datetime

app = Flask(__name__)

# DB configuration
MYSQL_CONFIG = {
    'host': '192.168.86.240',
    'user': 'birdnet_user',
    'password': 'Birdnetfoobar69!',
    'database': 'birdcall',
    'port': 3307
}

@app.route('/')
def index():
    try:
        conn = mariadb.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, species, confidence
            FROM detections
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('index.html', detections=rows)
    except mariadb.Error as err:
        return f"Database error: {err}", 500

@app.route('/summary')
def summary():
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        conn = mariadb.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT species, count(*) as count
            FROM detections
            WHERE DATE(timestamp) = ?
            GROUP BY species
            ORDER BY count DESC
        """, (date,))
        summary_data = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(summary_data)
    except mariadb.Error as err:
        return jsonify({"error": str(err)}), 500

@app.route('/thumb')
def thumbnail():
    from urllib.parse import unquote
    species = unquote(request.args.get('species', ''))
    source = request.args.get('source', 'wikipedia')
    if not species:
        return redirect(url_for('static', filename='placeholder.png'))

    cache_dir = 'static/thumb_cache'
    os.makedirs(cache_dir, exist_ok=True)
    species_hash = hashlib.md5(f"{source}_{species}".encode()).hexdigest()
    cache_path = os.path.join(cache_dir, f"{species_hash}.jpg")

    if os.path.exists(cache_path):
        return send_file(cache_path, mimetype='image/jpeg')

    try:
        if source == 'wikidata':
            from urllib.parse import quote
            search_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={quote(species)}&language=en&format=json&type=item"
            search_resp = requests.get(search_url, timeout=6).json()
            if search_resp.get("search"):
                entity_id = search_resp["search"][0]["id"]
                entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
                entity_data = requests.get(entity_url, timeout=6).json()
                entity = entity_data.get("entities", {}).get(entity_id, {})
                claims = entity.get("claims", {})
                if "P18" in claims:
                    image_name = claims["P18"][0]["mainsnak"]["datavalue"]["value"]
                    commons_url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{image_name}?width=300"
                    img_resp = requests.get(commons_url, timeout=6)
                    with open(cache_path, 'wb') as f:
                        f.write(img_resp.content)
                    return send_file(cache_path, mimetype='image/jpeg')
        else:
            api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(species)}"
            resp = requests.get(api_url, timeout=4)
            data = resp.json()
            if 'thumbnail' in data and 'source' in data['thumbnail']:
                img_resp = requests.get(data['thumbnail']['source'], timeout=4)
                with open(cache_path, 'wb') as f:
                    f.write(img_resp.content)
                return send_file(cache_path, mimetype='image/jpeg')
    except Exception as e:
        print(f"Thumbnail error for {species} ({source}): {e}")

    return redirect(url_for('static', filename='placeholder.png'))

@app.route('/species/<path:name>')
def species_detail(name):
    try:
        from urllib.parse import unquote, quote
        name = unquote(name)
        from urllib.parse import quote
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(name)}"
        resp = requests.get(api_url, timeout=6)
        data = resp.json()
        return render_template("species.html", species=data, query=name)
    except Exception as e:
        print(f"Species fetch error: {e}")
        return render_template("species.html", species=None, query=name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
