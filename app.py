from flask import Flask, request, jsonify

app = Flask(__name__)

# Example Sudoku solve endpoint
@app.route("/solve", methods=["POST"])
def solve():
    board = request.json.get("board")  # 9x9 list of lists or similar
    # TODO: call your solver here
    solution = board  # replace with real solution
    return jsonify({"solution": solution})

@app.route("/")
def health():
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)  # Render forwards to your PORT
