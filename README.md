# MVP

NEO4J query tool using natural language

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/insight-bridge-ai/MVP.git
cd MVP
```

2. Requirements:

```bash

# Activate the virtual environment
source venv/bin/activate

#Install Requirements
pip install -r requirements.txt

```

## Environment Setup

Create a `.env` file in the root directory and add the following environment variables:

1. **env Configuration**:

```
NEO4J_URI = ""
NEO4J_USERNAME = ""
NEO4J_PASSWORD = ""
NEO4J_DATABASE = ""
groq_api_key=""
```

2. **Running the Application**:


```bash

python3 main.py


```
