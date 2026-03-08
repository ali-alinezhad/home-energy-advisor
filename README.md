# Home Energy Advisor

A project built with FastAPI, SQLite, Vue 3, and TypeScript.
Users can create a home profile, retrieve it later, and generate AI-backed energy-efficiency recommendations.

## Tech stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- SQLite
- OpenAI SDK
- Pytest

### Frontend
- Vue 3
- TypeScript
- Vite
- Axios

## Features

- Create and save a home profile
- Retrieve a saved home profile by ID
- Generate 3 prioritized recommendations with an LLM
- Generate fresh advice on demand for the same saved home profile
- Store the latest generated advice on the home record
- Validate LLM output with Pydantic
- Support mock LLM mode for review without API access
- One-command local setup and run via `run.sh`

## Quick start

The easiest way to run the project is:

```bash
bash run.sh
```

This command:
- installs backend and frontend dependencies
- creates a root `.env` from `.env.example` if needed
- creates `web/.env` from `web/.env.example` if needed
- runs backend tests
- builds the frontend
- starts backend and frontend servers
- opens the app in the browser

By default, `.env.example` enables `MOCK_LLM=true`, so the app returns deterministic mock advice even if `LLM_API_KEY` is also set.
To use the real OpenAI integration, set `MOCK_LLM=false` and provide a valid OpenAI `LLM_API_KEY` in the root `.env`, then rerun `bash run.sh` (or restart the backend if it is already running).

Useful options:

```bash
bash run.sh --check-only   # install deps, run tests, and build the frontend without starting servers
bash run.sh --fresh-db     # remove the local SQLite database, then start backend/frontend and open the app
bash run.sh --fresh-db --no-open   # same as above, but do not open the browser automatically
```

Default URLs:

```text
Frontend: http://127.0.0.1:5173
Backend docs: http://127.0.0.1:8000/docs
```

## How the form works

The UI has one lookup action and two main actions:

- `Load Saved Profile`
  - fetches an existing home by ID
  - fills the form with that home's details
  - if that home already has saved advice, the latest advice is shown immediately with a small label
  - saved-advice timestamps are formatted using `VITE_DISPLAY_TIMEZONE` from `web/.env` (default: `Europe/Berlin`) in 24-hour local time

- `Create Home`
  - creates and saves a new home profile from the current form values
  - returns a new home ID
  - this is the step users should take after changing the form values

- `Generate Advice`
  - always requests a fresh LLM response for the currently saved home profile
  - saves that new result as the home's latest advice
  - updates the advice panel with the fresh result

- `Retry Generate Advice`
  - only appears after an advice-generation error
  - retries the same fresh advice request

## Manual setup

### Backend

```bash
python3 -m pip install -r requirements.txt
cp .env.example .env
python3 -m uvicorn app.main:app --reload
```

### Frontend

```bash
cd web
cp .env.example .env
npm install
npm run dev
```

## API endpoints

- `POST /api/homes` — create a home profile
- `GET /api/homes/{id}` — retrieve a home profile
- `POST /api/homes/{id}/advice` — generate fresh recommendations and save the latest advice

### Example create request

```json
{
  "size": 120,
  "year_built": 1985,
  "heating_type": "gas",
  "insulation_level": "medium"
}
```

### Example advice response

```json
{
  "recommendations": [
    {
      "title": "Seal air leaks",
      "description": "Seal drafty doors, windows, and loft penetrations to reduce avoidable heat loss.",
      "priority": "high"
    },
    {
      "title": "Upgrade attic insulation",
      "description": "Increase attic insulation depth to improve comfort and cut heating demand.",
      "priority": "medium"
    },
    {
      "title": "Install smart heating controls",
      "description": "Add programmable controls to reduce heating runtime when rooms are unused.",
      "priority": "low"
    }
  ]
}
```

## Project structure

```text
home-energy-advisor/
├── app/
│   ├── api/
│   ├── core/
│   │   ├── logging.py
│   │   └── settings.py
│   ├── db/
│   ├── llm/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── var/
├── web/
│   ├── .env.example
│   └── src/
├── .env.example
├── run.sh
├── requirements.txt
└── README.md
```

## Configuration

Runtime configuration is centralized in `app/core/settings.py`.
That file defines typed settings and fallback defaults.
The backend reads overrides from the root `.env` file.
The frontend reads overrides from `web/.env`.

### Root backend `.env`

```env
LLM_API_KEY=
MOCK_LLM=true
LOG_TO_FILE=true
```

### Frontend `web/.env`

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_DISPLAY_TIMEZONE=Europe/Berlin
```

## Notes

- The UI separates `Create Home` and `Generate Advice` so saving and AI generation are explicit actions.
- Loading a saved home also shows its latest saved advice when available.
- The API stores `year_built` as the stable home field, and the advice prompt also includes derived approximate home age to give the LLM clearer context.

## Tradeoffs

- SQLite was chosen for zero setup.
- Auth and deployment were intentionally skipped.
- The latest generated advice is stored on the `home` record instead of modeled as separate advice history.
- Styling is intentionally minimal.
- The current real integration uses the OpenAI SDK, while mock mode keeps the review path easy without external credentials.

## What I would improve next

- Add Alembic migrations
- Add frontend component tests
- Use provider-native structured output support
- Add retry/backoff for transient LLM failures
- Add multi-provider LLM support instead of a single OpenAI integration
- Store advice generations separately with prompt/model versioning
- Add stronger observability around LLM failures and latency
- Expand the home profile with more inputs like climate region and home type
- Add authentication and rate limiting if the product expands beyond the take-home scope

## AI Tool Usage Log

### Tools used
- GitHub Copilot

### Effective prompts
- “Propose a clean FastAPI structure for a small REST API with routes, services, schemas, and SQLite persistence.”
- “Suggest a prompt for home energy advice that returns exactly 3 short, prioritized recommendations in valid JSON.”
- “Review this small full-stack codebase and suggest pragmatic improvements to structure, API design, configuration, and developer experience without overengineering it.”
- “Review this Vue form flow and suggest a simpler way to handle create-home, reuse the current home profile when appropriate, and surface API errors clearly.”

### What AI helped with
- scaffolding repetitive backend and frontend boilerplate
- suggesting alternative prompt wording for the LLM request
- proposing refactors after the core flow was already defined
- speeding up small implementation details and cleanup

### What I owned
- the overall architecture and API design
- the decision to keep the solution small and aligned to the take-home scope
- the request/response contracts and validation rules
- the LLM prompt contract and structured output handling
- the persistence approach and caching behavior
- the frontend interaction flow and UX tradeoffs
- testing, debugging, and final code review decisions

### One thing AI got wrong
One generated frontend iteration reused the same `homeId` even after the user changed the form values.
That caused later requests to reference the previous home profile instead of creating a new one for the updated input.
I fixed that by comparing a snapshot of the submitted form state and creating a new home profile whenever the data changed.
