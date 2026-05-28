# AI Product Designer Agent on Amazon Bedrock — FCJ Workshop

A First Cloud Journey (FCJ) style workshop that builds and deploys a **generative-AI Product Designer agent** on **Amazon Bedrock**. Describe a product in plain language and the agent returns a structured design brief **and a generated product mockup image** — fully serverless and reproducible.

This repo contains both the **workshop documentation** (Hugo site) and the **deployable infrastructure** (AWS CDK).

## Layout

```
.
├── config.toml              # Hugo site config (theme: hugo-theme-relearn, variant: workshop)
├── content/5-Workshop/      # Workshop pages 5.1–5.7 (English + Vietnamese _index.vi.md)
├── assets/css/              # AWS-orange "workshop" theme variant
├── static/images/           # Diagrams + screenshots
├── themes/hugo-theme-relearn/  # Theme (git submodule)
└── infra/                   # AWS CDK (Python) app — Docker-free
    ├── app.py
    ├── stacks/              # agent_stack, api_stack, web_stack
    ├── agent/instruction.txt
    ├── lambda/              # generate_image, invoke_agent (zip, boto3 only)
    └── web/                 # static SPA (index.html, app.js, style.css)
```

## Architecture

`Browser → CloudFront → S3 (SPA)` and `Browser → API Gateway → Lambda → Bedrock Agent → (action group) Lambda → Stability Stable Image → S3 → CloudFront`.

- **Region:** `us-west-2` (the active region for Bedrock text-to-image; Amazon's image models are now Legacy).
- **Models:** Anthropic Claude (agent reasoning) + `stability.stable-image-core-v1:1` (image generation).
- **No Docker:** all Lambdas are zip packages whose only dependency, `boto3`, ships in the Lambda runtime.

## Quick start

### Preview the docs

```bash
git clone --recurse-submodules <repo-url>
cd aws-fcj-product-design-agent
hugo server
# open http://localhost:1313
```

### Deploy the workshop infrastructure

See **content/5-Workshop/5.2-prerequisite** for the full prerequisites, then:

```bash
cd infra
python -m venv .venv && source .venv/Scripts/activate   # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cdk bootstrap aws://<ACCOUNT_ID>/us-west-2
cdk deploy --all --require-approval never
```

Tear everything down with `cdk destroy --all` (empty the images bucket first).

## Notes

- The theme is **hugo-theme-relearn**, the maintained successor to the FCJ template's `hugo-theme-learn` (which is incompatible with current Hugo).
- The web API is open + CORS-permissive for workshop simplicity. For production, add authentication (Amazon Cognito) and request throttling.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
