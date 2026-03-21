from flask import Flask, request
import dns.resolver

app = Flask(__name__)

def cek(domain):
    resolver = dns.resolver.Resolver()

    resolver.nameservers = ["180.131.144.144"]
    try:
        resolver.resolve(domain, "A")
        return "🟢 SAFE"
    except:
        pass

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
