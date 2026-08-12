# pyBible v1.0.0

# fuck AI, sorry jesus . . .

# learned csv handling, bit of flask and have a git repository now, 3 birds one stone

import os
import csv
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'bibleDb.csv')

url = "https://labs.bible.org/api/?passage=random&type=json"

# Verse fetcher

def getRandomVerse():
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        raw_data = response.json()
        
        text = str(raw_data[0]['text'])
        bookname = str(raw_data[0]['bookname'])
        chapter = str(raw_data[0]['chapter'])
        verse = str(raw_data[0]['verse'])

        verse_list = [text, bookname, chapter, verse]
        verse_str = f"{text}\n{bookname} {chapter}:{verse}"
        return verse_list, verse_str
    except Exception as e:
        print("An error occurred fetching verse:", e)
        return None, None

# DB maker

def createDB():
    try:
        with open(DB_PATH, 'w', newline='', encoding='utf-8') as f:
            writerObj = csv.writer(f)
            writerObj.writerow(['text', 'bookname', 'chapter', 'verse'])
    except Exception as e:
        print("An error occurred:", e)

# Read CSV with UTF-8 1st, fallback -> non-UTF8 bytes

def safe_read_csv():
    if not os.path.exists(DB_PATH):
        return []
    try:
        with open(DB_PATH, 'r', newline='', encoding='utf-8') as f:
            return list(csv.reader(f))
    except UnicodeDecodeError:
        with open(DB_PATH, 'r', newline='', encoding='cp1252', errors='replace') as f:
            return list(csv.reader(f))

def writeToDB(verse_data):
    try:
        verse_str_data = [str(x) for x in verse_data]

        rows = safe_read_csv()
        for row in rows:
            if row == verse_str_data:
                return "exists"

        with open(DB_PATH, 'a', newline='', encoding='utf-8') as f:
            writerObj = csv.writer(f)
            writerObj.writerow(verse_data)
        return "success"

    except Exception as e:
        print("An error occurred:", e)
        return "error"

def searchFromDB(query):
    try:
        rows = safe_read_csv()
        if not rows:
            return 'No Verse Was Found ... '

        # Skip header if present
        if rows and rows[0] == ['text', 'bookname', 'chapter', 'verse']:
            rows = rows[1:]

        out_list = []
        found = False

        for i in rows:
            if not i:
                continue
            row_lower = [x.lower() for x in i]
            for cell in row_lower:
                if query.lower() in cell:
                    verse_text = row_lower[0]
                    verse_details = " ".join(row_lower[1:])
                    if not verse_text or not verse_details:
                        return 'No Verse Was Found ... '

                    found = True
                    out_text = f"{verse_text}\n{verse_details}\n\n"
                    out_list.append(out_text)
                    break

        if not found:
            return 'No Verse Was Found ... '
        else:
            return '\n'.join(out_list)
    except Exception as e:
        return f"An error occurred: {e}"

if not os.path.exists(DB_PATH):
    createDB()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/random', methods=['GET'])
def api_random():
    verse_list, verse_str = getRandomVerse()
    if verse_list is None:
        return jsonify({"status": "error", "message": "Failed to fetch verse from API"}), 500
    return jsonify({"verse_list": verse_list, "verse_str": verse_str})

@app.route('/api/save', methods=['POST'])
def api_save():
    data = request.json or {}
    verse_list = data.get('verse_list')
    if verse_list:
        status = writeToDB(verse_list)
        if status == "success":
            return jsonify({"status": "success", "message": "Saved to database"})
        elif status == "exists":
            return jsonify({"status": "exists", "message": "Already in database"})
        else:
            return jsonify({"status": "error", "message": "Failed to write to file"}), 500
    return jsonify({"status": "error", "message": "No data provided"}), 400

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.json or {}
    query = data.get('query', '')
    result = searchFromDB(query)
    return jsonify({"result": result})

@app.route('/api/clear', methods=['POST'])
def api_clear():
    createDB()
    return jsonify({"status": "success", "message": "Database cleared"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)