import json
import os
import uuid

import boto3

agent_rt = boto3.client("bedrock-agent-runtime")

AGENT_ID = os.environ["AGENT_ID"]
AGENT_ALIAS_ID = os.environ["AGENT_ALIAS_ID"]

# CORS headers are added by the Function URL's CORS config, so the handler
# only needs to declare the content type.
HEADERS = {"Content-Type": "application/json"}


def _resp(status, payload):
    return {"statusCode": status, "headers": HEADERS, "body": json.dumps(payload)}


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _resp(400, {"error": "invalid JSON body"})

    prompt = (body.get("prompt") or "").strip()
    if not prompt:
        return _resp(400, {"error": "missing 'prompt'"})
    session_id = body.get("sessionId") or uuid.uuid4().hex

    try:
        resp = agent_rt.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=prompt,
        )
        chunks = [ev["chunk"]["bytes"].decode("utf-8") for ev in resp["completion"] if "chunk" in ev]
        answer = "".join(chunks)
    except Exception as exc:  # surface Bedrock errors to the browser instead of a generic 500
        return _resp(502, {"error": str(exc)})

    return _resp(200, {"answer": answer, "sessionId": session_id})
