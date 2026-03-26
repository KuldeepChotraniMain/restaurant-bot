"""
run.py — development entry point

    python run.py

For production, point gunicorn at the factory:

    gunicorn "app:create_app()" --bind 0.0.0.0:8000
"""

from config import Config
from app import create_app

if __name__ == "__main__":
    flask_app = create_app()

    print("☕  aosa Bakehouse & Roastery — http://127.0.0.1:5000")
    print(f"🔑  Admin password : {Config.ADMIN_PASSWORD}")
    print(f"🤖  Gemini         : {'✅  ready' if Config.GOOGLE_API_KEY else '⚠️   set GOOGLE_API_KEY in .env'}")

    flask_app.run(debug=Config.DEBUG, port=5000)
