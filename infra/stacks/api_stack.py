from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_iam as iam,
    aws_lambda as _lambda,
)
from constructs import Construct


class ApiStack(Stack):
    """Lambda + Function URL that invokes the Bedrock agent for the browser.

    A Lambda Function URL is used instead of API Gateway because the agent's
    reason-then-generate-image loop runs ~35-45s, which exceeds API Gateway's
    hard 30s integration timeout. Function URLs honor the Lambda timeout (120s).
    """

    def __init__(self, scope: Construct, cid: str, *, agent_id: str, agent_alias_id: str, **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)

        invoke_fn = _lambda.Function(
            self,
            "InvokeAgentFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda/invoke_agent"),
            timeout=Duration.seconds(120),
            memory_size=256,
            environment={"AGENT_ID": agent_id, "AGENT_ALIAS_ID": agent_alias_id},
        )
        invoke_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeAgent"],
                resources=[f"arn:aws:bedrock:{self.region}:{self.account}:agent-alias/{agent_id}/{agent_alias_id}"],
            )
        )

        fn_url = invoke_fn.add_function_url(
            auth_type=_lambda.FunctionUrlAuthType.NONE,
            invoke_mode=_lambda.InvokeMode.BUFFERED,
            cors=_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_methods=[_lambda.HttpMethod.POST],
                allowed_headers=["content-type"],
            ),
        )

        self.api_url = fn_url.url
        CfnOutput(self, "ApiUrl", value=fn_url.url)
