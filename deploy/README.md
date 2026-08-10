# Deployment

Hosting is **not required** by the assignment — the deliverable is a public
GitHub repo link plus a demo video. These configs exist because a live URL in
your README is a cheap credibility win, and because it is useful for your
portfolio afterwards.

Every option needs `OPENAI_API_KEY` set as a platform secret. Never commit it.

## Option 1 — Streamlit Community Cloud (easiest, free)

Best fit: this is a Streamlit app, and Streamlit Cloud is built for exactly this.

1. Push this repo to GitHub, public.
2. Go to https://share.streamlit.io and sign in with GitHub.
3. New app -> pick this repo -> main file `app.py`.
4. Advanced settings -> Secrets, paste:
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```
5. Deploy. You get `https://<name>.streamlit.app`.

Caveat: the container filesystem is ephemeral, so `chroma_db/` is wiped on
restart. Press "Index the two files in data/" once after a cold start. Both
PDFs ship in `data/`, so this takes one click.

## Option 2 — Render (free tier, both services)

```bash
# from the repo root
cp deploy/render.yaml render.yaml
git add render.yaml && git commit -m "Add Render blueprint" && git push
```

Then on Render: New -> Blueprint -> select the repo. Set `OPENAI_API_KEY` when
prompted. Deploys the Streamlit UI and the FastAPI service as two web services.

Caveat: free instances sleep after 15 minutes idle and take ~50s to wake. Hit
the URL a minute before recording or demoing.

## Option 3 — Docker (anywhere)

```bash
docker build -f deploy/Dockerfile -t supplychain-rag .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... supplychain-rag
```

## What about Vercel?

Vercel is serverless and suits the FastAPI half at a push, but not Streamlit,
which needs a long-lived stateful process with websockets. Use Streamlit Cloud
or Render instead.

## Cost warning

A public URL with your key behind it means anyone who finds it can spend your
OpenAI credit. For a graded submission that is usually fine, but consider:

- Setting a low monthly usage cap in the OpenAI dashboard.
- Enabling password protection (Streamlit Cloud supports this on private apps).
- Taking the deployment down after grading.
