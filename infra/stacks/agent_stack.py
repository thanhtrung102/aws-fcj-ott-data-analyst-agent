from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_bedrock as bedrock,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_s3 as s3,
)
from constructs import Construct

DEFAULT_AGENT_MODEL = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
DEFAULT_GLUE_DATABASE = "fpt_ott_searchevents_analytics"
_INSTRUCTION = (Path(__file__).resolve().parent.parent / "agent" / "instruction.txt").read_text(encoding="utf-8")


class AgentStack(Stack):
    """Bedrock OTT Data Analyst agent + Glue/Athena action group."""

    def __init__(self, scope: Construct, cid: str, **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)

        agent_model = self.node.try_get_context("agentModel") or DEFAULT_AGENT_MODEL
        glue_database = self.node.try_get_context("glueDatabase") or DEFAULT_GLUE_DATABASE

        results_bucket = s3.Bucket(
            self,
            "ResultsBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(expiration=Duration.days(14), prefix="results/")
            ],
        )

        tools_fn = _lambda.Function(
            self,
            "GlueAthenaToolsFn",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="handler.handler",
            code=_lambda.Code.from_asset("lambda/glue_athena_tools"),
            timeout=Duration.seconds(120),
            memory_size=512,
            environment={
                "RESULTS_BUCKET": results_bucket.bucket_name,
                "ATHENA_WORKGROUP": "primary",
            },
        )
        results_bucket.grant_read_write(tools_fn)
        tools_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "athena:StartQueryExecution",
                    "athena:GetQueryExecution",
                    "athena:GetQueryResults",
                    "athena:StopQueryExecution",
                    "athena:GetWorkGroup",
                ],
                resources=["*"],
            )
        )
        tools_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "glue:GetDatabase",
                    "glue:GetDatabases",
                    "glue:GetTable",
                    "glue:GetTables",
                    "glue:GetPartition",
                    "glue:GetPartitions",
                ],
                resources=["*"],
            )
        )
        tools_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["lakeformation:GetDataAccess"],
                resources=["*"],
            )
        )
        tools_fn.add_permission(
            "AllowBedrockInvoke",
            principal=iam.ServicePrincipal("bedrock.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=self.account,
            source_arn=f"arn:aws:bedrock:{self.region}:{self.account}:agent/*",
        )

        agent_role = iam.Role(self, "AgentRole", assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"))
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                resources=["*"],
            )
        )
        agent_role.add_to_policy(
            iam.PolicyStatement(
                actions=["bedrock:GetInferenceProfile"],
                resources=[f"arn:aws:bedrock:*:{self.account}:inference-profile/*"],
            )
        )

        agent = bedrock.CfnAgent(
            self,
            "Agent",
            agent_name="OttDataAnalyst",
            agent_resource_role_arn=agent_role.role_arn,
            foundation_model=agent_model,
            instruction=_INSTRUCTION,
            idle_session_ttl_in_seconds=600,
            auto_prepare=True,
            action_groups=[
                bedrock.CfnAgent.AgentActionGroupProperty(
                    action_group_name="DataAnalystTools",
                    action_group_executor=bedrock.CfnAgent.ActionGroupExecutorProperty(
                        lambda_=tools_fn.function_arn,
                    ),
                    function_schema=bedrock.CfnAgent.FunctionSchemaProperty(
                        functions=[
                            bedrock.CfnAgent.FunctionProperty(
                                name="get_tables",
                                description="List all tables in a Glue database. Use this when you need to discover what tables are available.",
                                parameters={
                                    "database": bedrock.CfnAgent.ParameterDetailProperty(
                                        type="string",
                                        required=True,
                                        description=f"Glue database name. Default for this workshop: {glue_database}",
                                    ),
                                },
                            ),
                            bedrock.CfnAgent.FunctionProperty(
                                name="get_table",
                                description="Get the schema (columns, types, partition keys, S3 location) of a specific Glue table. Use this before writing SQL when you are unsure of a column name or type.",
                                parameters={
                                    "database": bedrock.CfnAgent.ParameterDetailProperty(
                                        type="string",
                                        required=True,
                                        description=f"Glue database name (default {glue_database}).",
                                    ),
                                    "table": bedrock.CfnAgent.ParameterDetailProperty(
                                        type="string",
                                        required=True,
                                        description="Table name (e.g. 'curated').",
                                    ),
                                },
                            ),
                            bedrock.CfnAgent.FunctionProperty(
                                name="athena_query",
                                description="Run a Presto/Trino SQL query against Amazon Athena and return the rows. Always include a partition filter on dt to keep scans cheap.",
                                parameters={
                                    "query": bedrock.CfnAgent.ParameterDetailProperty(
                                        type="string",
                                        required=True,
                                        description="A SQL SELECT statement. Use fully-qualified table names (database.table).",
                                    ),
                                    "database": bedrock.CfnAgent.ParameterDetailProperty(
                                        type="string",
                                        required=True,
                                        description=f"Default Glue database for unqualified table refs (default {glue_database}).",
                                    ),
                                    "timeout_seconds": bedrock.CfnAgent.ParameterDetailProperty(
                                        type="integer",
                                        required=False,
                                        description="Max wait time in seconds (default 90).",
                                    ),
                                },
                            ),
                        ]
                    ),
                )
            ],
        )

        alias = bedrock.CfnAgentAlias(self, "Alias", agent_id=agent.attr_agent_id, agent_alias_name="live")

        self.agent_id = agent.attr_agent_id
        self.agent_alias_id = alias.attr_agent_alias_id

        CfnOutput(self, "AgentId", value=agent.attr_agent_id)
        CfnOutput(self, "AgentAliasId", value=alias.attr_agent_alias_id)
        CfnOutput(self, "ResultsBucketName", value=results_bucket.bucket_name)
        CfnOutput(self, "GlueDatabase", value=glue_database)
