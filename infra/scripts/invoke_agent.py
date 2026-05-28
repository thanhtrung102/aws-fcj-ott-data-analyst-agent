"""Headless CLI to invoke the deployed OTT Data Analyst agent.

Usage:
    python scripts/invoke_agent.py "Top 10 search keywords in the 14-day window"

Reads the agent id/alias from the OttDataAnalystAgentStack CloudFormation outputs.
"""
import sys
import uuid

import boto3

REGION = "ap-southeast-1"
STACK = "OttDataAnalystAgentStack"


def stack_outputs():
    cf = boto3.client("cloudformation", region_name=REGION)
    outputs = cf.describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


def main():
    prompt = " ".join(sys.argv[1:]).strip() or (
        "Top 10 search keywords overall in the 14-day window, including any genre. Show counts."
    )
    out = stack_outputs()
    rt = boto3.client("bedrock-agent-runtime", region_name=REGION)
    resp = rt.invoke_agent(
        agentId=out["AgentId"],
        agentAliasId=out["AgentAliasId"],
        sessionId=uuid.uuid4().hex,
        inputText=prompt,
    )
    text = "".join(ev["chunk"]["bytes"].decode("utf-8") for ev in resp["completion"] if "chunk" in ev)
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")


if __name__ == "__main__":
    main()
