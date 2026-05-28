"""Headless CLI to invoke the deployed Product Designer agent.

Usage:
    python scripts/invoke_agent.py "Design a reusable bamboo water bottle for students"

Reads the agent id/alias from the ProductDesignerAgentStack CloudFormation outputs.
"""
import sys
import uuid

import boto3

REGION = "us-west-2"
STACK = "ProductDesignerAgentStack"


def stack_outputs():
    cf = boto3.client("cloudformation", region_name=REGION)
    outputs = cf.describe_stacks(StackName=STACK)["Stacks"][0]["Outputs"]
    return {o["OutputKey"]: o["OutputValue"] for o in outputs}


def main():
    prompt = " ".join(sys.argv[1:]).strip() or (
        "Design a reusable bamboo water bottle for Vietnamese university students."
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
