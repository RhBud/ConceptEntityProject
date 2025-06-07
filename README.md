# Concept Entity Project

Assessment Overview:
For this project you will be given a basic prompt and a sample list of 150+ clinical concepts that
need definitions in standard medical coding terminology.
Your task is to develop a service along with the appropriate evaluations that can generate
accurate clinical definitions given an input containing the concept name (e.g., congestive heart
failure) and concept type (e.g., diagnosis). The output will eventually need to be integrated back
into the CDL and ChatRWD.

Detailed Requirements:
1. Select an appropriate technology stack that you are familiar with to develop the service
   and develop a system diagram outlining the stack; be prepared to to describe your
   choice(s)
2. Connect the application to one or more LLMs using industry standard methods (or be
   ready to explain why you chose to deviate from those standards)
3. Develop an appropriate evaluation approach to identify errors and improve the prompt's
   performance in generating accurate clinical definitions. Please show the results of your
   evaluation and what you changed as a result.
4. Author a "final" version of the prompt that performs the task more accurately than the
   original (ideally with quantitative justification)
5. List the limitations of your implementation and/or discussion topics regarding how to
   make the service more robust for the future


This application consists of multiple Docker services:
- MongoDB: Database service
- Ontology Service: FastAPI service for entity processing
- Miniconda: Jupyter notebook environment


The Analysis is stored in the notebooks folder in order:

notebook0_load_mongo.ipynb -> basic code from other work to load MRCONSO table into the mongo service database for use

notebook1_eda_annotate.ipynb -> Just a quick look at the codes. I outline my strategy and perform the manual annotation for the project

notebook2_default_model.ipynb -> Define/justify labeling approach and rules, and evaluation metrics. Run and evaluate the model with OpenAPI gpt-4-turbo. Not good performance

notebook3_improve_model_best_iteration.ipynb -> Review results from default model and refine prompt and LLM strategy
- One term at a time
- Add a reviewer model to force only a few additional negatives (dont code)
- Add a function to look up some ingredients for RxNorm codes -> that was really the only way to improve model

Limitations and Discussion at the end of notebook3_improve_model_best_iteration.ipynb

## Prerequisites

- Windows 11
- Docker Desktop for Windows
- Docker Compose (V2)
- Python 3.8+ (for local development)

Note: This project uses the modern `docker compose` command syntax (with a space). The older `docker-compose` syntax (with a hyphen) is not used.

## Initial Setup

1. Create the required data directories in your Windows user profile:
   ```powershell
   # Create DOCKER_DATA structure
   mkdir -Force $env:USERPROFILE\DOCKER_DATA\mongodb
   mkdir -Force $env:USERPROFILE\DOCKER_DATA\ollama

   # Create pipeline_datalake directory
   mkdir -Force $env:USERPROFILE\pipeline_datalake
   ```

2. Create a `.docker_pipeline.env` file in your Windows user profile directory (`%USERPROFILE%`) with the following content:
   ```bash
   # MongoDB Configuration
   MONGO_INITDB_ROOT_USERNAME=any_username
   MONGO_INITDB_ROOT_PASSWORD=any_password
   MONGO_INITDB_DATABASE=operations

   # API Configuration
   API_ENV=development

   # OpenAI Configuration
   OPENAI_KEY=your_openai_key_here

   # HuggingFace Configuration
   HUGGINGFACE_KEY=your_huggingface_key_here
   ```

   Note: The `.docker_pipeline.env` file should be created in your Windows user profile directory (`%USERPROFILE%\.docker_pipeline.env`), not in the repository.

## Project Structure
```
.
├── docker/
│   ├── mongodb/
│   ├── api/
│   └── miniconda/
├── notebooks/
└── docker-compose.yml
```

## Data Storage

### Persistent Data (%USERPROFILE%\DOCKER_DATA\)
Each service stores its persistent data in dedicated directories:
- MongoDB: `%USERPROFILE%\DOCKER_DATA\mongodb`
- Ollama: `%USERPROFILE%\DOCKER_DATA\ollama`

### Shared Data Lake (%USERPROFILE%\pipeline_datalake\)
- Mounted as `/pipeline_datalake` in all services
- Used for:
  - Raw data files
  - Shared data access between services
  - Data processing results

## Docker Compose Profiles

The application supports two different deployment profiles:

### Local Profile
Basic setup with essential services:
- MongoDB
- Ontology Service
- Miniconda

To use:
```bash
docker compose --profile local up -d
```

### Local-Extended Profile
Full local development setup with all services:
- All services from Local profile
- Ollama

To use:
```bash
docker compose --profile local-ext up -d
```

## Setup and Usage

1. Build the containers:
   ```bash
   docker compose --profile local build
   ```

2. Launch the services using your desired profile:
   ```bash
   # For basic local development
   docker compose --profile local up -d

   # For full local setup with all services
   docker compose --profile local-ext up -d
   ```

3. To stop services:
   ```bash
   # Stop all services
   docker compose down

   # Stop specific profile
   docker compose --profile local down
   ```

4. Access the services:
   - MongoDB: localhost:27018
   - Ontology Service: http://localhost:8000
   - Miniconda/Jupyter: http://localhost:8888

## Service Details

### MongoDB
- Port: 27018 (mapped to container port 27017)
- Default database: operations
- Persistent data storage in `%USERPROFILE%\DOCKER_DATA\mongodb`
- Shared data access at `/pipeline_datalake`

### Ontology Service
- API Documentation: http://localhost:8000/docs
- Swagger UI: http://localhost:8000/redoc
- Endpoints:
  - /health: Health check endpoint
  - /process: Data processing endpoint
- Shared data access at `/pipeline_datalake`

### Miniconda/Jupyter
- Jupyter Notebook: http://localhost:8888
- Default token: develop
- Notebooks directory mounted at `/app/notebooks`
- Shared data access at `/pipeline_datalake`