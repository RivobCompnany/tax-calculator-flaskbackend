import os
import sys
from flask import Flask, jsonify
from flask_cors import CORS

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sars.routes.tax import tax_bp


def create_app():
    app = Flask(__name__)

    # Configure CORS to allow your GitHub Pages site and Render domain
    CORS(app, origins=[
        "https://rivobcompnany.github.io",
        "https://tax-calculator-flaskbackend.onrender.com",  # Allow Render backend
        "http://localhost:*",  # for local development
        "http://127.0.0.1:*"
    ], supports_credentials=True)
    
    app.register_blueprint(tax_bp, url_prefix='/api')
    
    @app.route("/")
    def health_check():
        return jsonify({
            "status": "ok",
            "message": "Tax Calculator API is running"
        })

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)