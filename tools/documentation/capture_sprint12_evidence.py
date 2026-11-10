"""Repete os fluxos completos na versão final, preservando o histórico anterior."""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("API_URL", "http://127.0.0.1:8022")
os.environ.setdefault("APP_URL", "http://127.0.0.1:5192")
os.environ.setdefault("EVIDENCE_DIR", str(ROOT / "docs/sprint-12"))
import capture_sprint11_evidence as previous
if __name__ == "__main__":
    previous.main()
