import json
import redis
import os


# ==========================
# Configuration
# ==========================
REDIS_HOST = "localhost"
REDIS_PORT = 6379
TOP_K = 2


# ==========================
# Load Patient JSON
# ==========================
def load_patient_profile():
    path = os.path.join(os.path.dirname(__file__), "patient.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

ISSUE_KEYWORDS = {
    "postpartum anxiety": [
        "postpartum", "maternal", "after childbirth", "pregnancy"
    ],
    "anxiety": [
        "anxiety", "panic", "stress", "cbt"
    ],
    "adhd": [
        "adhd", "attention", "hyperactivity", "child"
    ],
    "addiction": [
        "addiction", "alcohol", "drug", "rehabilitation"
    ],
    "workplace stress": [
        "workplace", "burnout", "executive", "professional"
    ]
}

SEVERITY_MULTIPLIER = {
    "low": 0.7,
    "medium": 1.0,
    "high": 1.3
}

# ==========================
# Scoring Functions
# ==========================
def score_specialization(patient_issue, doctor_specialization, doctor_bio, severity):
    text = f"{doctor_specialization} {doctor_bio}".lower()
    keywords = ISSUE_KEYWORDS.get(patient_issue.lower(), [])

    for kw in keywords:
        if kw in text:
            base_score = 40
            multiplier = SEVERITY_MULTIPLIER.get(severity.lower(), 1.0)
            return round(base_score * multiplier, 2)

    return 0


def score_language(preferred_language, doctor_languages):
    return 20 if preferred_language in doctor_languages else 0


def score_availability(required_mode, doctor_mode):
    return 15 if required_mode == doctor_mode else 0


def score_budget(max_budget, doctor_fee):
    return 15 if doctor_fee <= max_budget else 0


def score_rating(rating):
    return round((rating / 5) * 10, 2)


# ==========================
# Recommendation Engine
# ==========================
def recommend_doctors():
    patient = load_patient_profile()

    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )
    r.ping()

    results = []

    for key in r.scan_iter("doctor:*"):
        doc = r.hgetall(key)

        languages = json.loads(doc["languages"])
        fee = float(doc["fee"])
        rating = float(doc["rating"])

        spec_score = score_specialization(
            patient["primary_issue"],
            doc["specialization"],
            doc.get("bio", ""),
            patient["severity"]
        )

        lang_score = score_language(
            patient["preferred_language"],
            languages
        )

        avail_score = score_availability(
            patient["consultation_mode"],
            doc["availability"]
        )

        budget_score = score_budget(
            patient["budget"],
            fee
        )

        rating_score = score_rating(rating)

        final_score = min(
            spec_score +
            lang_score +
            avail_score +
            budget_score +
            rating_score,
            100
        )

        results.append({
            "doctor_id": doc["doctor_id"],
            "name": doc["name"],
            "specialization": doc["specialization"],
            "rating": rating,
            "fee": fee,
            "availability": doc["availability"],
            "score_breakdown": {
                "specialization": spec_score,
                "language": lang_score,
                "availability": avail_score,
                "budget": budget_score,
                "rating": rating_score
            },
            "final_score": round(final_score, 2)
        })

    results.sort(
        key=lambda x: (
            x["final_score"],                       # primary
            x["score_breakdown"]["specialization"], # tie-breaker 1
            x["rating"],                            # tie-breaker 2
            -x["fee"]                               # tie-breaker 3 (lower fee wins)
        ),
        reverse=True
    )
    return results[:TOP_K]


# ==========================
# Run
# ==========================
if __name__ == "__main__":
    recommendations = recommend_doctors()

    print("\n🏥 Recommended Doctors (Top 2)\n")

    for i, d in enumerate(recommendations, 1):
        print(f"{i}. {d['name']}")
        print(f"   Specialization : {d['specialization']}")
        print(f"   Rating         : {d['rating']}")
        print(f"   Fee            : ₹{d['fee']}")
        print(f"   Availability   : {d['availability']}")
        print("   Score Breakdown:")
        print(f"     - Specialization : {d['score_breakdown']['specialization']}")
        print(f"     - Language       : {d['score_breakdown']['language']}")
        print(f"     - Availability   : {d['score_breakdown']['availability']}")
        print(f"     - Budget         : {d['score_breakdown']['budget']}")
        print(f"     - Rating         : {d['score_breakdown']['rating']}")
        print(f"   ➜ Final Score     : {d['final_score']}/100\n")
