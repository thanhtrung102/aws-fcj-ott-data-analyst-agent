#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.agent_stack import AgentStack
from stacks.api_stack import ApiStack
from stacks.web_stack import WebStack

region = os.environ.get("CDK_DEPLOY_REGION", "ap-southeast-1")
env = cdk.Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), region=region)

app = cdk.App()

agent = AgentStack(app, "OttDataAnalystAgentStack", env=env)

api = ApiStack(
    app,
    "OttDataAnalystApiStack",
    agent_id=agent.agent_id,
    agent_alias_id=agent.agent_alias_id,
    env=env,
)
api.add_dependency(agent)

web = WebStack(app, "OttDataAnalystWebStack", api_url=api.api_url, env=env)
web.add_dependency(api)

app.synth()
