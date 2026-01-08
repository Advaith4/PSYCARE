# Doctor Recommendation System – Psycare

A rule-based doctor recommendation engine for the Psycare project that intelligently matches patients with suitable healthcare providers using explainable scoring mechanisms.

## Overview

This recommendation system is designed as an independent, testable module that suggests the **top 2 most suitable doctors** for a patient based on structured patient profiles. It employs a transparent, rule-based scoring algorithm with configurable severity weighting and tie-breaker logic.

**Current Status:** Development & Validation Phase (Static Data)

---

## Key Features

- **Rule-Based Recommendation Logic** – Transparent, deterministic scoring algorithm
- **Explainable Scoring** – Detailed breakdown of recommendation scores for clinical validation
- **Severity-Based Weighting** – Clinical relevance through severity adjustment multipliers
- **Deterministic Ranking** – Consistent results with well-defined tie-breaker rules
- **Redis-Backed Storage** – Fast, in-memory data retrieval
- **Static Data Testing** – Safe iteration independent of production databases

---

## Scoring System

### Scoring Criteria

The recommendation algorithm evaluates doctors across five key dimensions:

| Criterion | Max Score | Description |
|-----------|-----------|-------------|
| Specialization Relevance | 40 | Match between patient issue and doctor expertise |
| Language Preference | 20 | Doctor's proficiency in patient's preferred language |
| Consultation Mode | 15 | Availability in online/offline format |
| Budget Compatibility | 15 | Alignment with patient's budget constraints |
| Doctor Rating | 10 | Patient satisfaction and quality metrics |
| **Total** | **100** | – |

### Severity-Based Weighting

Specialization scores are adjusted based on the patient's condition severity:

| Severity Level | Multiplier | Use Case |
|---|---|---|
| Low | 0.7× | Minor concerns, general guidance |
| Medium | 1.0× | Standard clinical assessment |
| High | 1.3× | Urgent, complex, or critical conditions |

### Tie-Breaker Logic

When multiple doctors have identical final scores, ranking is determined by:

1. **Higher specialization score** – Clinical expertise priority
2. **Higher doctor rating** – Patient satisfaction
3. **Lower consultation fee** – Cost efficiency

---

## Project Structure

```
PSYCARE/
├── Docker-Compose.yml              # Redis containerization
├── README.md                        # This file
├── recommendation_system/
│   ├── v1/                         # Prototype: Basic data storage
│   │   ├── doctors.json
│   │   └── store_doctors.py
│   ├── v2/                         # Development: Data ingestion & embeddings
│   │   ├── doctors.json
│   │   ├── doctors_with_embeddings.json
│   │   └── store_doctors.py
│   ├── v3/                         # Production: Final recommendation engine
│   │   ├── patient.json            # Sample patient profile
│   │   └── recommend.py            # Main recommendation script
│   └── redis_checker.py            # Redis connectivity diagnostic
```

---

## Input & Output

### Input: Patient Profile

The system accepts a structured JSON profile representing the patient's requirements and constraints:

```json
{
  "primary_issue": "ADHD",
  "severity": "medium",
  "preferred_language": "English",
  "consultation_mode": "Offline",
  "budget": 700
}
```

**Profile Fields:**
- `primary_issue` – Patient's primary medical concern
- `severity` – Condition severity: `low`, `medium`, or `high`
- `preferred_language` – Preferred consultation language
- `consultation_mode` – Preferred delivery method: `Online` or `Offline`
- `budget` – Maximum consultation fee (in local currency)

### Output: Recommendations

The system outputs the top 2 recommended doctors with comprehensive score details:

```
1. Dr. Kavya Rao
   Score Breakdown:
     - Specialization : 40
     - Language       : 20
     - Availability   : 15
     - Budget         : 15
     - Rating         : 9.4
   ➜ Final Score     : 99.4/100

2. Dr. Priya Sharma
   Score Breakdown:
     - Specialization : 38
     - Language       : 20
     - Availability   : 15
     - Budget         : 15
     - Rating         : 8.9
   ➜ Final Score     : 96.9/100
```

---

## Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for Redis)
- Redis client library: `pip install redis`

### Installation & Execution

**Step 1: Start Redis**

```bash
docker compose up -d
```

**Step 2: Load Doctor Data**

```bash
cd recommendation_system/v2
python store_doctors.py
```

**Step 3: Run Recommendations**

```bash
cd ../v3
python recommend.py
```

### Verification

To verify Redis connectivity:

```bash
python recommendation_system/redis_checker.py
```

---

## Architecture & Design

### Why Static Data?

The current implementation uses static doctor datasets for:

- **Controlled Testing** – Predictable, reproducible results
- **Safe Experimentation** – Risk-free iteration on scoring algorithms
- **Clear Validation** – Simplified verification of recommendation logic
- **Development Independence** – No dependency on production systems

### Migration Path

The system is architected for easy migration to live data sources:

- **Current:** JSON-based static data + Redis
- **Future:** Direct MongoDB/PostgreSQL integration
- **Extensible:** Modular design supports additional data sources

---

## Development Versions

| Version | Purpose | Status |
|---------|---------|--------|
| **v1** | Initial prototype with basic storage | Reference only |
| **v2** | Data ingestion pipeline with embeddings | Active development |
| **v3** | Final recommendation engine | Production-ready |

---

## Contributing

Improvements and suggestions are welcome. When contributing:

1. Maintain the explainability of the scoring system
2. Update documentation for algorithmic changes
3. Test with the static dataset before deployment
4. Preserve deterministic behavior for consistency

---

