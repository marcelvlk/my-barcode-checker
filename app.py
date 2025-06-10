from flask import Flask, request, render_template, send_file, jsonify
import os, uuid, csv, threading, time
from scraper import scrape_prices

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
LOG_FOLDER = "logs"
RESULT_FOLDER = "results"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Store job data in memory
job_store = {}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["barcode_file"]
        if not file or not file.filename.endswith(".csv"):
            return "Invalid file. Please upload a .csv file.", 400

        job_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_FOLDER, f"{job_id}.csv")
        file.save(input_path)

        log_path = os.path.join(LOG_FOLDER, f"{job_id}.log")
        result_path = os.path.join(RESULT_FOLDER, f"{job_id}_results.csv")

        # Store paths for client to use
        job_store[job_id] = {
            "log": log_path,
            "result": result_path,
            "status": "processing"
        }

        threading.Thread(target=scrape_prices, args=(input_path, result_path, log_path, job_id)).start()
        return render_template("progress.html", job_id=job_id)

    return render_template("index.html")

@app.route("/log/<job_id>")
def get_log(job_id):
    log_path = job_store.get(job_id, {}).get("log")
    if not log_path or not os.path.exists(log_path):
        return "", 204
    with open(log_path, "r", encoding="utf-8") as f:
        return f.read()

@app.route("/result/<job_id>")
def get_result(job_id):
    result_path = job_store.get(job_id, {}).get("result")
    if not result_path or not os.path.exists(result_path):
        return "Results not ready yet.", 202
    with open(result_path, newline='', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    return render_template("result.html", rows=rows)

@app.route("/download/<job_id>")
def download_result(job_id):
    result_path = job_store.get(job_id, {}).get("result")
    if result_path and os.path.exists(result_path):
        return send_file(result_path, as_attachment=True)
    return "No result found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
