import redis, json
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
r = redis.Redis(host="localhost", port=6379, decode_responses=True)

with open("doctors.json") as f:
    doctors = json.load(f)

for doc in doctors:
    text = doc["specialization"] + " " + doc["bio"]
    vector = model.encode(text).tolist()

    r.hset(f"doctor:{doc['doctor_id']}", mapping={
        "doctor_id": doc["doctor_id"],
        "name": doc["name"],
        "specialization": doc["specialization"],
        "rating": doc["rating"],
        "fee": doc["fee"],
        "languages": json.dumps(doc["languages"]),
        "availability": doc["availability"],
        "embedding": json.dumps(vector)
    })

print("Stored doctors in Redis!")
