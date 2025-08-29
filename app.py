import base64
import hashlib
import json
from flask import Flask, request, jsonify
from mcrcon import MCRcon

app = Flask(__name__)

# LiqPay ключі
LIQPAY_PUBLIC = "sandbox_i28524890692"
LIQPAY_PRIVATE = "sandbox_N1zqYl44YbkLIpj73bEujO3kYSpdDiwMooSpyLAZ"

# RCON
RCON_HOST = "server228.zapto.org"
RCON_PORT = 25575
RCON_PASSWORD = "Vlad20137777bo208goasfjmJkhgJn"

def liqpay_sign(data):
    return base64.b64encode(
        hashlib.sha1((LIQPAY_PRIVATE + data + LIQPAY_PRIVATE).encode()).digest()
    ).decode()

@app.route("/donate", methods=["POST"])
def donate():
    data = request.form.get("data")
    signature = request.form.get("signature")

    if not data or not signature:
        return jsonify({"error": "no data"}), 400

    # перевірка підпису
    if signature != liqpay_sign(data):
        return jsonify({"error": "bad signature"}), 400

    decoded = json.loads(base64.b64decode(data).decode())
    print("📩 LiqPay callback:", decoded)

    if decoded.get("status") == "success":
        nickname = decoded.get("info")  # у LiqPay можна передати нік
        rank = "BADBOY"  # приклад — можна прив'язати до суми

        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                command = f"lp user {nickname} parent set {rank}"
                resp = mcr.command(command)
                print(f"✅ Видано {rank} гравцю {nickname}: {resp}")
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"error": "RCON error", "details": str(e)}), 500
    else:
        return jsonify({"status": "not paid"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
