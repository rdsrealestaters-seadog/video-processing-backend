from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Backend is running"

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    return jsonify({"status": "received", "data": data})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
