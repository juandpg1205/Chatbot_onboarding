# Articles Chatbot (proof of concept)

A small chatbot that answers questions using **only** the PDFs you give it as its knowledge
base (for example IT support articles about Macs, Avaya, SAP, device setup). The interface and
the answers are English only.

It uses **Gemini API File Search**, a managed RAG service: Google chunks, embeds and searches
the PDFs, so there is no vector database to run.

![stack](https://img.shields.io/badge/stack-Flask%20%2B%20Gemini%20File%20Search-blue)

## Features

- Chat UI with a "thinking" animation (typing dots and status phases) and a typewriter effect.
- Answers include the source PDFs as chips.
- Access code login, so you can share the page with one person.
- Automatic fallback to other Gemini models when one is overloaded (429/503/504) or times out.
- Guardrails based on the OWASP Top 10 for LLM Applications (see below).

## Requirements

- Python 3.10+
- A Google AI Studio API key (free tier is enough for a small test)
- A few PDFs to use as the knowledge base

## Setup

1. Get an API key: open https://aistudio.google.com, choose **Get API key**, then **Create API key**.
   A Google AI Pro subscription does not include API access; the AI Studio key is separate.
2. Install and configure:

```bash
git clone <this-repo-url>
cd Articles_Chatbot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env with your API key and an access code
```

3. Put your PDFs in the `articles/` folder (or set `ARTICLES_DIR` in `.env`).
4. Index the PDFs (once, and again whenever you add new ones):

```bash
python ingest.py
```

5. Run the app and open http://127.0.0.1:5001:

```bash
python app.py
```

Sign in with the `ACCESS_CODE` from your `.env`.

## Configuration (`.env`)

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google AI Studio API key. |
| `GEMINI_MODEL` | Primary model (default `gemini-3.5-flash`). Fallbacks are defined in `app.py`. |
| `ACCESS_CODE` | Code required on the sign-in page. |
| `ARTICLES_DIR` | Folder with the PDFs (default `./articles`). |

Never commit `.env`. It is already in `.gitignore`.

## Project structure

| File | Purpose |
|---|---|
| `ingest.py` | Uploads the PDFs to a File Search store. Resumable: skips files already uploaded. |
| `app.py` | Flask server: login, chat UI and the `POST /api/chat` endpoint. |
| `store.json` | Generated. Name of your File Search store and the uploaded files. Not versioned. |
| `articles/` | Put your PDFs here. Their contents are not versioned. |

To re-index from scratch, delete `store.json` (and the old store in AI Studio), then run `python ingest.py`.

## Sharing it temporarily

To let one person try it, you can expose the local app with a Cloudflare quick tunnel:

```bash
brew install cloudflared                          # macOS; see Cloudflare docs for other systems
cloudflared tunnel --url http://127.0.0.1:5001    # prints https://<random>.trycloudflare.com
```

Send the URL and the access code through different channels. The URL changes every time the
tunnel restarts, and your computer must stay on while it is shared. Stop the tunnel to cut access.

## Security controls (OWASP Top 10 for LLM Applications)

| Risk | Control |
|---|---|
| LLM01 Prompt injection | Restrictive system instruction: answer only from the documents, refuse other topics, ignore instructions to change the rules or reveal the prompt. |
| LLM02 Sensitive information disclosure | Only the PDFs you index are searchable. Review them for credentials and personal data first. |
| LLM05 Improper output handling | The browser renders answers with `textContent`, never as HTML. |
| LLM06 Excessive agency | The model only has the read-only File Search tool. |
| LLM07 System prompt leakage | The system prompt contains no secrets. |
| LLM09 Misinformation | An answer with no citations from the documents is discarded and replaced by a refusal. |
| LLM10 Unbounded consumption | 500 characters per question, 10 requests per minute per IP, 800 output tokens, login attempt limit. |

Also: HttpOnly session cookie, constant-time access code comparison, and internal errors are not shown to users.

English only: the system prompt tells the model to reply in English, and the server answers
"Please ask your question in English." when the question contains non-ASCII letters (accents, other alphabets).

## Known limitations

- **No conversation memory.** Each question is independent.
- **Overload errors.** Google may return 429/503/504 on the free tier. The app tries fallback models
  and shows a "high demand" message if all fail. A slow chain of fallbacks can exceed 100 s, which
  makes a Cloudflare tunnel close the connection.
- **Model names change often.** On a 404 model error, set `GEMINI_MODEL` to a model your key can use
  (list them with `client.models.list()`).
- **In-memory rate limits** reset when the app restarts.
- **File names** with non-ASCII characters are uploaded with a normalized name, because the SDK sends
  the file name in an HTTP header.
- Only a small set of prompt-injection attempts was tested. Do more testing before wider use.

## Privacy

On the free tier of the Gemini API, Google may use the data you send to improve its products. Index
only documents you are allowed to share outside your organization. For sensitive or production use,
use an enterprise offering with data-retention controls (for example RAG Engine on Google Cloud's
Gemini Enterprise Agent Platform) and replace the access code with your organization's SSO.

## License

Add a license of your choice before publishing (for example MIT).
