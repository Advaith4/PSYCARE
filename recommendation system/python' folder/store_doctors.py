import json
import sys
import traceback
from pathlib import Path

try:
    import redis
except ModuleNotFoundError:
    print("Missing dependency: redis. Install with: pip install redis", file 
          =sys.stderr)
    raise

# Defer importing sentence-transformers until runtime in load_model()
# to allow graceful fallback to TF-IDF when torch cannot be initialized on Windows.

MODEL_NAME = "all-MiniLM-L6-v2"
DOCTORS_FILE_DEFAULT = "doctors.json"

REQUIRED_KEYS = {"doctor_id", "name", "specialization", "bio", "rating", "fee", "languages", "availability"}


def load_model():
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(MODEL_NAME)
        return model, 'st'
    except Exception as e:
        print(f"SentenceTransformer unavailable ({e}). Falling back to TF-IDF vectorizer.", file=sys.stderr)
        return None, 'tfidf'


def load_doctors(path):
    try:
        if not path.exists():
            print(f"Doctors file not found: {path}", file=sys.stderr)
            raise FileNotFoundError(path)
        try:
            size = path.stat().st_size
        except Exception:
            size = None
        print(f"Reading doctors file (size={size}): {path}")

        with open(path, "r", encoding="utf-8-sig") as f:
            content = f.read()

        if not content or not content.strip():
            print(f"Doctors file appears empty (size={size}): {path}", file=sys.stderr)
            # attempt to show first bytes in case of odd encoding
            try:
                with open(path, "rb") as rb:
                    raw = rb.read(200)
                    print(f"First 200 bytes (raw): {raw[:200]!r}", file=sys.stderr)
            except Exception:
                pass
            raise ValueError(f"Doctors file is empty: {path}")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # print a small preview to help debugging
            preview = content[:400].replace("\n", " ")
            print(f"Invalid JSON in {path}: {e}. Preview: {preview}", file=sys.stderr)
            raise
    except FileNotFoundError:
        print(f"Doctors file not found: {path}", file=sys.stderr)
        raise


def connect_redis(host="localhost", port=6379):
    r = redis.Redis(host=host, port=port, decode_responses=True)
    try:
        r.ping()
        return r
    except Exception as e:
        print(f"Failed to connect to Redis at {host}:{port}: {e}", file=sys.stderr)
        return None


def validate_doc(doc):
    missing = REQUIRED_KEYS - set(doc.keys())
    if missing:
        raise KeyError(f"Missing keys in doctor entry: {missing}")


def main():
    # resolve doctors.json relative to this script to avoid cwd issues
    doctors_file = Path(__file__).resolve().parent / DOCTORS_FILE_DEFAULT
    print(f"Using doctors file: {doctors_file}")

    model, mode = load_model()
    r = connect_redis()

    doctors = load_doctors(doctors_file)

    texts = [f"{d.get('specialization','')} {d.get('bio','')}" for d in doctors]

    if mode == 'tfidf':
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
        except ModuleNotFoundError:
            print("Missing scikit-learn. Install with: pip install scikit-learn", file=sys.stderr)
            raise
        vectorizer = TfidfVectorizer()
        vectorizer.fit(texts)

    saved_entries = []

    for doc, text in zip(doctors, texts):
        try:
            validate_doc(doc)

            if mode == 'st':
                vector = model.encode(text).tolist()
            else:
                vector = vectorizer.transform([text]).toarray()[0].tolist()

            mapping = {
                "doctor_id": str(doc["doctor_id"]),
                "name": str(doc["name"]),
                "specialization": str(doc["specialization"]),
                "rating": str(doc["rating"]),
                "fee": str(doc["fee"]),
                "languages": json.dumps(doc["languages"]),
                "availability": str(doc["availability"]),
                "embedding": json.dumps(vector),
            }

            if r:
                r.hset(f"doctor:{doc['doctor_id']}", mapping=mapping)
            else:
                saved_entries.append(mapping)
        except Exception:
            print("Error processing doctor entry:", doc, file=sys.stderr)
            traceback.print_exc()
            # continue with next doctor

    if saved_entries:
        out_path = Path("doctors_with_embeddings.json")
        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(saved_entries, out_f, ensure_ascii=False, indent=2)
        print(f"Redis unavailable — saved {len(saved_entries)} entries to {out_path}")
    else:
        print("Stored doctors in Redis!")


if __name__ == "__main__":
    main()
