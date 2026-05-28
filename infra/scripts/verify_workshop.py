"""Post-deploy verification: 5 OTT analyst queries against 2022-06-01..06-14.

Runs the headless agent against five canonical questions, captures the
brief + the SQL the agent wrote + the rows returned, and prints them in
Markdown so the workshop docs can paste real outputs.
"""
import json
import os
import sys
import time
import urllib.request
import uuid

import boto3

REGION = "ap-southeast-1"
AGENT_STACK = "OttDataAnalystAgentStack"
API_STACK = "OttDataAnalystApiStack"
WEB_STACK = "OttDataAnalystWebStack"

QUESTIONS = [
    "Top 10 search keywords overall in the 14-day window, including any genre. Show counts.",
    "How does the genre mix differ between mobile, tv, and web platforms during the workshop window? Give percentages by platform.",
    "Which day in the workshop window had the highest abandon rate (is_search_abandoned=true), and what was that rate?",
    "List the top 10 UNKNOWN keywords by frequency in the workshop window.",
    "Which hour of day (hour_of_day_vn) has the highest search volume across the workshop window?",
]


def get_outputs(stack):
    cf = boto3.client("cloudformation", region_name=REGION)
    return {o["OutputKey"]: o["OutputValue"] for o in cf.describe_stacks(StackName=stack)["Stacks"][0].get("Outputs", [])}


def invoke_headless(rt, agent_id, alias_id, question):
    t0 = time.time()
    resp = rt.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=uuid.uuid4().hex,
        inputText=question,
        enableTrace=True,
    )
    text_chunks = []
    trace_events = []
    for ev in resp["completion"]:
        if "chunk" in ev:
            text_chunks.append(ev["chunk"]["bytes"].decode("utf-8"))
        if "trace" in ev:
            trace_events.append(ev["trace"])
    dt = time.time() - t0
    return "".join(text_chunks), trace_events, dt


def invoke_via_api(api_url, question):
    body = json.dumps({"prompt": question}).encode("utf-8")
    req = urllib.request.Request(api_url, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=180) as r:
        payload = json.loads(r.read())
    return r.status, payload, time.time() - t0


def main():
    agent_out = get_outputs(AGENT_STACK)
    api_out = get_outputs(API_STACK)
    web_out = get_outputs(WEB_STACK)
    agent_id = agent_out["AgentId"]
    alias_id = agent_out["AgentAliasId"]
    api_url = api_out["ApiUrl"]
    web_url = web_out["WebUrl"]

    print("# OTT Data Analyst Agent — Verification Report")
    print()
    print("## Stack outputs")
    for label, d in [("Agent", agent_out), ("Api", api_out), ("Web", web_out)]:
        print(f"### {label}")
        for k, v in d.items():
            if "ExportsOutput" in k:
                continue
            print(f"- **{k}** = `{v}`")
    print()

    print("## SPA reachability")
    for path in ["", "/index.html", "/app.js", "/style.css", "/config.js"]:
        url = web_url + path
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                print(f"- HTTP {r.status} {r.headers.get('Content-Type','')}  {path or '/'}")
        except Exception as e:
            print(f"- FAIL {path}: {e}")
    print()

    print("## config.js content")
    with urllib.request.urlopen(web_url + "/config.js", timeout=15) as r:
        cfg = r.read().decode("utf-8").strip()
        print(f"```\n{cfg}\n```")
        match = api_url in cfg
        print(f"Match ApiUrl: **{match}**")
    print()

    rt = boto3.client("bedrock-agent-runtime", region_name=REGION)

    print("## Headless agent invocations (5 canonical questions)\n")
    for i, q in enumerate(QUESTIONS, 1):
        print(f"### Q{i}: {q}\n")
        try:
            text, trace, dt = invoke_headless(rt, agent_id, alias_id, q)
        except Exception as e:
            print(f"FAILED: {e}\n")
            continue
        sqls = []
        for ev in trace:
            t = ev.get("trace", {})
            for k in ("orchestrationTrace", "agentTrace"):
                inner = t.get(k, {}) if isinstance(t, dict) else {}
                inv = inner.get("invocationInput", {}) if isinstance(inner, dict) else {}
                ag = inv.get("actionGroupInvocationInput", {}) if isinstance(inv, dict) else {}
                if ag.get("function") == "athena_query":
                    for p in ag.get("parameters", []) or []:
                        if p.get("name") == "query":
                            sqls.append(p.get("value", ""))
        if sqls:
            print("**SQL the agent ran:**")
            for s in sqls:
                print(f"```sql\n{s}\n```")
        print(f"**Latency:** {dt:.2f}s\n")
        print("**Agent answer:**")
        sys.stdout.buffer.write(text.encode("utf-8"))
        print("\n\n---\n")

    print("## Curl smoke test through Lambda Function URL\n")
    status, payload, dt = invoke_via_api(api_url, QUESTIONS[0])
    print(f"HTTP {status} in {dt:.2f}s, answer = {len(payload.get('answer',''))}B, sessionId = `{payload.get('sessionId','')}`")
    print()
    print("**First 600 chars of API answer:**")
    sys.stdout.buffer.write(payload.get("answer", "")[:600].encode("utf-8"))
    print("\n")
    print("## Live URLs")
    print(f"- **SPA:** {web_url}")
    print(f"- **API:** {api_url}")


if __name__ == "__main__":
    main()
