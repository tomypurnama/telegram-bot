from flask import Flask, request
from flask_cors import CORS
import dns.resolver

app = Flask(__name__)

# WAJIB: Biar bisa diakses dari GitHub Pages
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route("/")
def home():
    return "API RUNNING"

def cek(domain):
    resolver = dns.resolver.Resolver()

    # DNS Nawala
    resolver.nameservers = ["180.131.144.144"]
    try:
        resolver.resolve(domain, "A")
        return "🟢 SAFE"
    except:
        pass

    # Fallback DNS global
    resolver.nameservers = ["8.8.8.8"]
    try:
        resolver.resolve(domain, "A")
        return "🟢 SAFE"
    except:
        return "🔴 BLOCKED"

@app.route("/check")
def check():
    domain = request.args.get("domain")
    return cek(domain)

app.run(host="0.0.0.0", port=5000)
