\# EchoScript.AI Backend



\*\*Production‑grade FastAPI backend\*\* for the EchoScript.AI transcription platform. Supports audio/video transcription via WhisperX, AI enhancements (summaries, sentiment, keywords), user authentication (Auth0 JWT, password reset), subscriptions (Stripe), storage \& exports, and background utilities.



---



\## 🚀 Quick Start



1\. \*\*Clone the repo\*\*



&nbsp;  ```bash

&nbsp;  git clone https://github.com/Arizzo729/echoscript-backend.git

&nbsp;  cd echoscript-backend

&nbsp;  ```



2\. \*\*Create a Python 3.11 virtual environment\*\*



&nbsp;  ```bash

&nbsp;  python3.11 -m venv .venv# EchoScript.AI Backend



\*\*Production‑grade FastAPI backend\*\* for the EchoScript.AI transcription platform. Supports audio/video transcription via WhisperX, AI enhancements (summaries, sentiment, keywords), user authentication (Auth0 JWT, password reset), subscriptions (Stripe), storage \& exports, and background utilities.



---



\## 🚀 Quick Start



1\. \*\*Clone the repo\*\*



&nbsp;  ```bash

&nbsp;  git clone https://github.com/Arizzo729/echoscript-backend.git

&nbsp;  cd echoscript-backend

&nbsp;  ```



2\. \*\*Create a Python 3.11 virtual environment\*\*



&nbsp;  ```bash

&nbsp;  python3.11 -m venv .venv

&nbsp;  source .venv/bin/activate

&nbsp;  ```



3\. \*\*Install dependencies\*\*



&nbsp;  ```bash

&nbsp;  pip install pip-tools

&nbsp;  pip-compile requirements.in

&nbsp;  pip-sync requirements.txt

&nbsp;  ```



4\. \*\*Set up environment variables\*\*



&nbsp;  \* Copy `.env.example` to `.env`

&nbsp;  \* Fill in values (API keys, DB URL, Redis URL, JWT secret, etc.)



5\. \*\*Initialize the database\*\*



&nbsp;  ```bash

&nbsp;  python scripts/init\_db.py

&nbsp;  ```



6\. \*\*Run locally\*\*



&nbsp;  ```bash

&nbsp;  uvicorn main:app --reload --host 0.0.0.0 --port 8000

&nbsp;  ```



7\. \*\*Access the health check\*\*



&nbsp;  \* Open \[http://localhost:8000/](http://localhost:8000/) to verify the service is running.



---



\## 📁 Project Structure



```

├── Dockerfile

├── docker-compose.yml

├── requirements.in/.txt

├── .env.example

├── .gitignore

├── README.md

├── main.py

├── scripts/init\_db.py

├── app/

│   ├── db.py

│   ├── config.py

│   ├── dependencies.py

│   ├── models.py

│   ├── utils/

│   ├── routes/

│   └── ws/

└── tests/

&nbsp;   └── \[unit \& integration tests]

```



---



\## ⚙️ Environment Variables



Copy and edit `.env.example`:



```ini

\# .env.example

DATABASE\_URL=postgresql://user:pass@host:port/dbname

REDIS\_URL=redis://localhost:6379/0

OPENAI\_API\_KEY=your\_openai\_key

HF\_TOKEN=your\_huggingface\_token

STRIPE\_SECRET\_KEY=your\_stripe\_key

JWT\_SECRET\_KEY=supersecret

JWT\_ALGORITHM=HS256

FRONTEND\_URL=http://localhost:3000

DEBUG=True

```



---



\## 📦 Docker \& Docker Compose



\* \*\*Build \& run\*\*:



&nbsp; ```bash

&nbsp; docker-compose up --build

&nbsp; ```

\* \*\*Stop \& remove\*\*:



&nbsp; ```bash

&nbsp; docker-compose down

&nbsp; ```



---



\## 🔧 Development Tools



\* \*\*Pre-commit hooks\*\*: formatting, linting, type checks



&nbsp; ```bash

&nbsp; pre-commit install

&nbsp; ```

\* \*\*Run checks manually\*\*:



&nbsp; ```bash

&nbsp; pre-commit run --all-files

&nbsp; flake8 .

&nbsp; mypy app

&nbsp; bandit -r app

&nbsp; ```



---



\## 🧪 Testing



```bash

pytest --maxfail=1 --disable-warnings -q

```



---



\## CI/CD



GitHub Actions pipeline defined in `.github/workflows/ci.yml`:



\* Installs and pins dependencies via pip-tools

\* Runs pre-commit, flake8, mypy, bandit, pytest

\* Uploads coverage report artifact



---



\## 📄 License



This project is licensed under the MIT License. See \[LICENSE](./LICENSE) for details.



&nbsp;  source .venv/bin/activate

&nbsp;  ```



3\. \*\*Install dependencies\*\*



&nbsp;  ```bash

&nbsp;  pip install pip-tools

&nbsp;  pip-compile requirements.in

&nbsp;  pip-sync requirements.txt

&nbsp;  ```



4\. \*\*Set up environment variables\*\*



&nbsp;  \* Copy `.env.example` to `.env`

&nbsp;  \* Fill in values (API keys, DB URL, Redis URL, JWT secret, etc.)



5\. \*\*Initialize the database\*\*



&nbsp;  ```bash

&nbsp;  python scripts/init\_db.py

&nbsp;  ```



6\. \*\*Run locally\*\*



&nbsp;  ```bash

&nbsp;  uvicorn main:app --reload --host 0.0.0.0 --port 8000

&nbsp;  ```



7\. \*\*Access the health check\*\*



&nbsp;  \* Open \[http://localhost:8000/](http://localhost:8000/) to verify the service is running.



---



\## 📁 Project Structure



```

├── Dockerfile

├── docker-compose.yml

├── requirements.in/.txt

├── .env.example

├── .gitignore

├── README.md

├── main.py

├── scripts/init\_db.py

├── app/

│   ├── db.py

│   ├── config.py

│   ├── dependencies.py

│   ├── models.py

│   ├── utils/

│   ├── routes/

│   └── ws/

└── tests/

&nbsp;   └── \[unit \& integration tests]

```



---



\## ⚙️ Environment Variables



Copy and edit `.env.example`:



```ini

\# .env.example

DATABASE\_URL=postgresql://user:pass@host:port/dbname

REDIS\_URL=redis://localhost:6379/0

OPENAI\_API\_KEY=your\_openai\_key

HF\_TOKEN=your\_huggingface\_token

STRIPE\_SECRET\_KEY=your\_stripe\_key

JWT\_SECRET\_KEY=supersecret

JWT\_ALGORITHM=HS256

FRONTEND\_URL=http://localhost:3000

DEBUG=True

```



---



\## 📦 Docker \& Docker Compose



\* \*\*Build \& run\*\*:



&nbsp; ```bash

&nbsp; docker-compose up --build

&nbsp; ```

\* \*\*Stop \& remove\*\*:



&nbsp; ```bash

&nbsp; docker-compose down

&nbsp; ```



---



\## 🔧 Development Tools



\* \*\*Pre-commit hooks\*\*: formatting, linting, type checks



&nbsp; ```bash

&nbsp; pre-commit install

&nbsp; ```

\* \*\*Run checks manually\*\*:



&nbsp; ```bash

&nbsp; pre-commit run --all-files

&nbsp; flake8 .

&nbsp; mypy app

&nbsp; bandit -r app

&nbsp; ```



---



\## 🧪 Testing



```bash

pytest --maxfail=1 --disable-warnings -q

```



---



\## CI/CD



GitHub Actions pipeline defined in `.github/workflows/ci.yml`:



\* Installs and pins dependencies via pip-tools

\* Runs pre-commit, flake8, mypy, bandit, pytest

\* Uploads coverage report artifact



---



\## 📄 License



This project is licensed under the MIT License. See \[LICENSE](./LICENSE) for details.
