# Concept Entity Project

A FastAPI-based medical entity recognition and coding service that identifies medical concepts and maps them to appropriate medical vocabularies (ICD-10, CPT, LOINC, RxNorm, ATC).

## Overview

This service uses LLMs to analyze medical concepts and return structured responses with:
- Entity type classification (diagnosis, procedure, medication, etc.)
- Medical codes from appropriate vocabularies
- Confidence scores for each code
- Human-readable descriptions

## Architecture

- **FastAPI Service**: REST API for entity analysis
- **MongoDB**: Medical vocabulary database (UMLS/RxNorm data)
- **OpenAI GPT-4**: LLM for entity recognition and coding
- **Docker**: Containerized deployment (Linux containers)

## Quick Start

### Prerequisites

- **Docker**: Version 20.10+ with Docker Compose V2
- **Docker Compose**: Version 2.0+ (included with Docker Desktop)
- **OpenAI API key**: Valid API key for GPT-4 access
- **Bash shell**: For running setup commands
- **Disk space**: At least 5GB free space for containers and data

### Required Directory Structure

The application expects these directories to exist in your home directory:

```bash
# Create required directories
mkdir -p ~/DOCKER_DATA/mongodb
mkdir -p ~/DOCKER_DATA/ollama
mkdir -p ~/pipeline_datalake
```

### Setup

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/ConceptEntityProject.git
cd ConceptEntityProject
```

2. **Create environment file:**
```bash
# Create ~/.docker_pipeline.env with required environment variables
cat > ~/.docker_pipeline.env << EOF
# MongoDB Configuration
MONGO_INITDB_ROOT_USERNAME=admin
MONGO_INITDB_ROOT_PASSWORD=password
MONGO_INITDB_DATABASE=operations

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# API Configuration
API_ENV=development
EOF
```

3. **Build and start services:**
```bash
docker compose --profile local build
docker compose --profile local up -d
```

4. **Verify the service is running:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{"status": "healthy", "mongodb": "connected"}
```

## API Usage

### Analyze Medical Entity

**Endpoint:** `POST /analyze-entity`

**Example - Diagnosis:**
```bash
curl -X POST "http://localhost:8000/analyze-entity" \
  -H "Content-Type: application/json" \
  -d '{"concept_name": "Myocardial infarction"}'
```

**Response:**
```json
{
  "entities": {
    "Myocardial infarction": {
      "entity_name": "Myocardial infarction",
      "types": "diagnosis",
      "codes": [
        {
          "code": "I21",
          "system": "ICD-10",
          "description": "Acute myocardial infarction",
          "confidence": 100
        }
      ]
    }
  }
}
```

**Example - Medication:**
```bash
curl -X POST "http://localhost:8000/analyze-entity" \
  -H "Content-Type: application/json" \
  -d '{"concept_name": "Aspirin"}'
```

**Response:**
```json
{
  "entities": {
    "Aspirin": {
      "entity_name": "Aspirin",
      "types": "medication",
      "codes": [
        {
          "code": "1191",
          "system": "RxNorm",
          "description": "Aspirin",
          "confidence": 100
        }
      ]
    }
  }
}
```

### Health Check

```bash
curl http://localhost:8000/health
```

### Get Processed Data

```bash
curl http://localhost:8000/entityDefinition
```

## Testing

Run the test suite to verify functionality:

```bash
cd docker/ontology-svc
python test_api.py
```

Or run with pytest for detailed output:

```bash
pytest test_api.py -v
```

## Supported Entity Types

- **Diagnosis**: ICD-10, ICD-10-CM
- **Procedure**: CPT
- **Medication**: RxNorm
- **Lab/Measurement**: LOINC
- **Drug Class**: ATC

## Project Structure

```
ontology-svc/
├── app/
│   ├── main.py           # FastAPI app initialization
│   ├── api/
│   │   └── endpoints.py  # API routes
│   ├── core/
│   │   └── entity.py     # Business logic
│   └── models/
│       └── schemas.py    # Pydantic models
├── requirements.txt
├── Dockerfile
└── test_api.py
```

## Development

### Rebuilding the Service

After code changes:

```bash
docker compose --profile local build ontology-svc
docker compose --profile local up -d
```

### Viewing Logs

```bash
docker compose --profile local logs ontology-svc
```

### Stopping Services

```bash
docker compose --profile local down
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 8000, 27018, and 8888 are available
2. **Permission errors**: Make sure you have write access to `~/DOCKER_DATA` and `~/pipeline_datalake`
3. **Environment file**: Verify `~/.docker_pipeline.env` exists and contains valid API keys
4. **Docker version**: Ensure Docker Compose V2 is available (`docker compose version`)

### Service Ports

- **Ontology Service**: http://localhost:8000
- **MongoDB**: localhost:27018
- **Jupyter Notebook**: http://localhost:8888 (token: `develop`)

## Notes

- Built and tested on macOS, but runs in Linux containers
- Requires OpenAI API key for LLM functionality
- MongoDB contains UMLS/RxNorm medical vocabulary data
- Service is conservative in coding - prefers accuracy over coverage
- Uses Docker Compose V2 syntax (space, not hyphen)

## License

[Add your license information here]