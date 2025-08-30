import base64
import hashlib
import json
import time
from flask import Flask, request, jsonify
from mcrcon import MCRcon
from flask_cors import CORS  # <-- додали CORS

app = Flask(__name__)
CORS(app)  # <-- дозволяємо запити з будь-якого домену (для тесту можна обмежити пізніше)

# LiqPay ключі
LIQPAY_PUBLIC = "sandbox_i28524890692"
LIQPAY_PRIVATE = "sandbox_N1zqYl44YbkLIpj73bEujO3kYSpdDiwMooSpyLAZ"

# RCON
RCON_HOST = "server228.zapto.org"
RCON_PORT = 25575
RCON_PASSWORD = "Vlad20137777bo208goasfjmJkhgJn"

# карта сум → ранг
PRICE_TO_RANK = {
    50: "BADBOY",
    100: "VIP",
    200: "LEGEND",
    500: "OVERLORD"
}

def liqpay_sign(data):
    return base64.b64encode(
        hashlib.sha1((LIQPAY_PRIVATE + data + LIQPAY_PRIVATE).encode()).digest()
    ).decode()

# Створення платежу
@app.route("/create-payment", methods=["POST"])
def create_payment():
    body = request.json
    amount = body.get("amount")
    description = body.get("description")
    nickname = body.get("nickname")

    if not amount or not description or not nickname:
        return jsonify({"error": "missing fields"}), 400

    payment = {
        "public_key": LIQPAY_PUBLIC,
        "action": "pay",
        "amount": amount,
        "currency": "UAH",
        "description": description,
        "order_id": str(int(time.time())),
        "version": "3",
        "info": nickname,
        "server_url": "https://web-production-0323.up.railway.app/donate"
    }

    data_str = base64.b64encode(json.dumps(payment).encode()).decode()
    signature = liqpay_sign(data_str)

    return jsonify({"data": data_str, "signature": signature})

# Callback від LiqPay
@app.route("/donate", methods=["POST"])
def donate():
    data = request.form.get("data")
    signature = request.form.get("signature")

    if not data or not signature:
        return jsonify({"error": "no data"}), 400

    if signature != liqpay_sign(data):
        return jsonify({"error": "bad signature"}), 400

    decoded = json.loads(base64.b64decode(data).decode())
    print("📩 LiqPay callback:", decoded)

    if decoded.get("status") == "success":
        nickname = decoded.get("info")
        amount = decoded.get("amount")
        rank = PRICE_TO_RANK.get(int(amount), "BADBOY")

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
