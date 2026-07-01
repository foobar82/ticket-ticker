"""Development entry point: `python run.py` (spec §5, single process)."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug server only -- internal network, single team (spec §1).
    app.run(host="0.0.0.0", port=5000, debug=True)
