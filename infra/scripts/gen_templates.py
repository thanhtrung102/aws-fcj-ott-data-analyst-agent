"""Generate the three CFN templates without invoking jsii/aws-cdk-lib.

The synth process OOMs on this constrained machine. Since we know the
exact resources we need (Bedrock Agent + 3 Lambdas + 2 S3 buckets +
CloudFront + Function URL), we write CFN directly.

Outputs go to cdk.out/<Stack>.template.json — the same paths
`aws cloudformation deploy --template-file` expects.
"""
import json
import os
import sys
from pathlib import Path

ACCT = "703668403514"
REGION = "ap-southeast-1"
BOOT_BUCKET = f"cdk-hnb659fds-assets-{ACCT}-{REGION}"
GLUE_DB = "fpt_ott_searchevents_analytics"
AGENT_MODEL = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

ASSET_TOOLS = "9aa12fbb1fbeaead78cc117778ac556cbf17d235f17ac662dde072f51ae28bd4"
ASSET_INVOKE = "910d43fa1962280b6864a431bcb0215ca54f943c6bf811cf688b49776c2dc862"

OUT_DIR = Path(__file__).resolve().parent.parent / "cdk.out"
OUT_DIR.mkdir(exist_ok=True)

INSTRUCTION = (Path(__file__).resolve().parent.parent / "agent" / "instruction.txt").read_text(encoding="utf-8")


def agent_stack():
    return {
        "Resources": {
            "ResultsBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketEncryption": {
                        "ServerSideEncryptionConfiguration": [
                            {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                        ]
                    },
                    "PublicAccessBlockConfiguration": {
                        "BlockPublicAcls": True, "BlockPublicPolicy": True,
                        "IgnorePublicAcls": True, "RestrictPublicBuckets": True,
                    },
                    "LifecycleConfiguration": {
                        "Rules": [{
                            "Id": "ExpireResults", "Status": "Enabled",
                            "Prefix": "results/", "ExpirationInDays": 14,
                        }]
                    },
                },
                "UpdateReplacePolicy": "Delete",
                "DeletionPolicy": "Delete",
            },
            "GlueAthenaToolsRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }],
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                    "Policies": [{
                        "PolicyName": "ToolsInline",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "athena:StartQueryExecution", "athena:GetQueryExecution",
                                        "athena:GetQueryResults", "athena:StopQueryExecution",
                                        "athena:GetWorkGroup",
                                    ],
                                    "Resource": "*",
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "glue:GetDatabase", "glue:GetDatabases",
                                        "glue:GetTable", "glue:GetTables",
                                        "glue:GetPartition", "glue:GetPartitions",
                                    ],
                                    "Resource": "*",
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": ["lakeformation:GetDataAccess"],
                                    "Resource": "*",
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": [
                                        "s3:PutObject", "s3:GetObject", "s3:DeleteObject",
                                        "s3:ListBucket", "s3:GetBucketLocation",
                                    ],
                                    "Resource": [
                                        {"Fn::GetAtt": ["ResultsBucket", "Arn"]},
                                        {"Fn::Join": ["", [{"Fn::GetAtt": ["ResultsBucket", "Arn"]}, "/*"]]},
                                    ],
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": ["s3:GetObject", "s3:ListBucket"],
                                    "Resource": [
                                        "arn:aws:s3:::fpt-ott-ap-southeast-1-703668403514-stage-prod",
                                        "arn:aws:s3:::fpt-ott-ap-southeast-1-703668403514-stage-prod/*",
                                    ],
                                },
                            ],
                        },
                    }],
                },
            },
            "GlueAthenaToolsFn": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "Architectures": ["arm64"],
                    "Code": {"S3Bucket": BOOT_BUCKET, "S3Key": f"{ASSET_TOOLS}.zip"},
                    "Environment": {
                        "Variables": {
                            "RESULTS_BUCKET": {"Ref": "ResultsBucket"},
                            "ATHENA_WORKGROUP": "primary",
                        }
                    },
                    "Handler": "handler.handler",
                    "MemorySize": 512,
                    "Role": {"Fn::GetAtt": ["GlueAthenaToolsRole", "Arn"]},
                    "Runtime": "python3.12",
                    "Timeout": 120,
                },
            },
            "GlueAthenaToolsBedrockPerm": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "Action": "lambda:InvokeFunction",
                    "FunctionName": {"Fn::GetAtt": ["GlueAthenaToolsFn", "Arn"]},
                    "Principal": "bedrock.amazonaws.com",
                    "SourceAccount": ACCT,
                    "SourceArn": f"arn:aws:bedrock:{REGION}:{ACCT}:agent/*",
                },
            },
            "AgentRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "bedrock.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }],
                    },
                    "Policies": [{
                        "PolicyName": "AgentInline",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Effect": "Allow",
                                    "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
                                    "Resource": "*",
                                },
                                {
                                    "Effect": "Allow",
                                    "Action": ["bedrock:GetInferenceProfile"],
                                    "Resource": f"arn:aws:bedrock:*:{ACCT}:inference-profile/*",
                                },
                            ],
                        },
                    }],
                },
            },
            "Agent": {
                "Type": "AWS::Bedrock::Agent",
                "Properties": {
                    "AgentName": "OttDataAnalyst",
                    "AgentResourceRoleArn": {"Fn::GetAtt": ["AgentRole", "Arn"]},
                    "FoundationModel": AGENT_MODEL,
                    "Instruction": INSTRUCTION,
                    "IdleSessionTTLInSeconds": 600,
                    "AutoPrepare": True,
                    "ActionGroups": [{
                        "ActionGroupName": "DataAnalystTools",
                        "ActionGroupExecutor": {
                            "Lambda": {"Fn::GetAtt": ["GlueAthenaToolsFn", "Arn"]}
                        },
                        "FunctionSchema": {
                            "Functions": [
                                {
                                    "Name": "get_tables",
                                    "Description": "List all tables in a Glue database. Use this when you need to discover what tables are available.",
                                    "Parameters": {
                                        "database": {
                                            "Type": "string", "Required": True,
                                            "Description": f"Glue database name. Default for this workshop: {GLUE_DB}",
                                        }
                                    },
                                },
                                {
                                    "Name": "get_table",
                                    "Description": "Get the schema (columns, types, partition keys, S3 location) of a specific Glue table.",
                                    "Parameters": {
                                        "database": {
                                            "Type": "string", "Required": True,
                                            "Description": f"Glue database name (default {GLUE_DB}).",
                                        },
                                        "table": {
                                            "Type": "string", "Required": True,
                                            "Description": "Table name (e.g. 'curated').",
                                        },
                                    },
                                },
                                {
                                    "Name": "athena_query",
                                    "Description": "Run a Presto/Trino SQL query against Amazon Athena and return the rows. Always include a partition filter on dt to keep scans cheap.",
                                    "Parameters": {
                                        "query": {
                                            "Type": "string", "Required": True,
                                            "Description": "A SQL SELECT statement. Use fully-qualified table names (database.table).",
                                        },
                                        "database": {
                                            "Type": "string", "Required": True,
                                            "Description": f"Default Glue database for unqualified table refs (default {GLUE_DB}).",
                                        },
                                        "timeout_seconds": {
                                            "Type": "integer", "Required": False,
                                            "Description": "Max wait time in seconds (default 90).",
                                        },
                                    },
                                },
                            ]
                        },
                    }],
                },
            },
            "AgentAlias": {
                "Type": "AWS::Bedrock::AgentAlias",
                "Properties": {
                    "AgentId": {"Fn::GetAtt": ["Agent", "AgentId"]},
                    "AgentAliasName": "live",
                },
            },
        },
        "Outputs": {
            "AgentId": {
                "Value": {"Fn::GetAtt": ["Agent", "AgentId"]},
                "Export": {"Name": "OttDataAnalystAgentStack:AgentId"},
            },
            "AgentAliasId": {
                "Value": {"Fn::GetAtt": ["AgentAlias", "AgentAliasId"]},
                "Export": {"Name": "OttDataAnalystAgentStack:AgentAliasId"},
            },
            "ResultsBucketName": {"Value": {"Ref": "ResultsBucket"}},
            "GlueDatabase": {"Value": GLUE_DB},
            "ToolsRoleArn": {"Value": {"Fn::GetAtt": ["GlueAthenaToolsRole", "Arn"]}},
        },
    }


def api_stack():
    return {
        "Resources": {
            "InvokeAgentRole": {
                "Type": "AWS::IAM::Role",
                "Properties": {
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }],
                    },
                    "ManagedPolicyArns": [
                        "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
                    ],
                    "Policies": [{
                        "PolicyName": "InvokeAgentInline",
                        "PolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [{
                                "Effect": "Allow",
                                "Action": "bedrock:InvokeAgent",
                                "Resource": {
                                    "Fn::Join": ["", [
                                        f"arn:aws:bedrock:{REGION}:{ACCT}:agent-alias/",
                                        {"Fn::ImportValue": "OttDataAnalystAgentStack:AgentId"},
                                        "/",
                                        {"Fn::ImportValue": "OttDataAnalystAgentStack:AgentAliasId"},
                                    ]]
                                },
                            }],
                        },
                    }],
                },
            },
            "InvokeAgentFn": {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "Architectures": ["arm64"],
                    "Code": {"S3Bucket": BOOT_BUCKET, "S3Key": f"{ASSET_INVOKE}.zip"},
                    "Environment": {
                        "Variables": {
                            "AGENT_ID": {"Fn::ImportValue": "OttDataAnalystAgentStack:AgentId"},
                            "AGENT_ALIAS_ID": {"Fn::ImportValue": "OttDataAnalystAgentStack:AgentAliasId"},
                        }
                    },
                    "Handler": "handler.handler",
                    "MemorySize": 256,
                    "Role": {"Fn::GetAtt": ["InvokeAgentRole", "Arn"]},
                    "Runtime": "python3.12",
                    "Timeout": 120,
                },
            },
            "InvokeAgentFnUrl": {
                "Type": "AWS::Lambda::Url",
                "Properties": {
                    "AuthType": "NONE",
                    "Cors": {
                        "AllowHeaders": ["content-type"],
                        "AllowMethods": ["POST"],
                        "AllowOrigins": ["*"],
                    },
                    "InvokeMode": "BUFFERED",
                    "TargetFunctionArn": {"Fn::GetAtt": ["InvokeAgentFn", "Arn"]},
                },
            },
            "InvokeAgentFnUrlPerm": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "Action": "lambda:InvokeFunctionUrl",
                    "FunctionName": {"Fn::GetAtt": ["InvokeAgentFn", "Arn"]},
                    "FunctionUrlAuthType": "NONE",
                    "Principal": "*",
                },
            },
            "InvokeAgentFnViaUrlPerm": {
                "Type": "AWS::Lambda::Permission",
                "Properties": {
                    "Action": "lambda:InvokeFunction",
                    "FunctionName": {"Fn::GetAtt": ["InvokeAgentFn", "Arn"]},
                    "InvokedViaFunctionUrl": True,
                    "Principal": "*",
                },
            },
        },
        "Outputs": {
            "ApiUrl": {
                "Value": {"Fn::GetAtt": ["InvokeAgentFnUrl", "FunctionUrl"]},
                "Export": {"Name": "OttDataAnalystApiStack:ApiUrl"},
            }
        },
    }


def web_stack(web_assets_hash):
    return {
        "Resources": {
            "WebBucket": {
                "Type": "AWS::S3::Bucket",
                "Properties": {
                    "BucketEncryption": {
                        "ServerSideEncryptionConfiguration": [
                            {"ServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
                        ]
                    },
                    "PublicAccessBlockConfiguration": {
                        "BlockPublicAcls": True, "BlockPublicPolicy": True,
                        "IgnorePublicAcls": True, "RestrictPublicBuckets": True,
                    },
                },
                "UpdateReplacePolicy": "Delete",
                "DeletionPolicy": "Delete",
            },
            "WebOAC": {
                "Type": "AWS::CloudFront::OriginAccessControl",
                "Properties": {
                    "OriginAccessControlConfig": {
                        "Name": {"Fn::Sub": "${AWS::StackName}-oac"},
                        "OriginAccessControlOriginType": "s3",
                        "SigningBehavior": "always",
                        "SigningProtocol": "sigv4",
                    }
                },
            },
            "WebCdn": {
                "Type": "AWS::CloudFront::Distribution",
                "Properties": {
                    "DistributionConfig": {
                        "Comment": "OTT Data Analyst web app",
                        "Enabled": True,
                        "DefaultRootObject": "index.html",
                        "DefaultCacheBehavior": {
                            "TargetOriginId": "WebOrigin",
                            "ViewerProtocolPolicy": "redirect-to-https",
                            "AllowedMethods": ["GET", "HEAD"],
                            "CachedMethods": ["GET", "HEAD"],
                            "Compress": True,
                            "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
                        },
                        "Origins": [{
                            "Id": "WebOrigin",
                            "DomainName": {"Fn::GetAtt": ["WebBucket", "RegionalDomainName"]},
                            "S3OriginConfig": {"OriginAccessIdentity": ""},
                            "OriginAccessControlId": {"Fn::GetAtt": ["WebOAC", "Id"]},
                        }],
                        "PriceClass": "PriceClass_100",
                    }
                },
            },
            "WebBucketPolicy": {
                "Type": "AWS::S3::BucketPolicy",
                "Properties": {
                    "Bucket": {"Ref": "WebBucket"},
                    "PolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [{
                            "Effect": "Allow",
                            "Principal": {"Service": "cloudfront.amazonaws.com"},
                            "Action": "s3:GetObject",
                            "Resource": {"Fn::Sub": "${WebBucket.Arn}/*"},
                            "Condition": {
                                "StringEquals": {
                                    "AWS:SourceArn": {
                                        "Fn::Sub": "arn:aws:cloudfront::${AWS::AccountId}:distribution/${WebCdn}"
                                    }
                                }
                            },
                        }],
                    },
                },
            },
        },
        "Outputs": {
            "WebUrl": {"Value": {"Fn::Sub": "https://${WebCdn.DomainName}"}},
            "WebBucketName": {"Value": {"Ref": "WebBucket"}},
        },
    }


def write(name, body):
    path = OUT_DIR / f"{name}.template.json"
    path.write_text(json.dumps(body, indent=1), encoding="utf-8")
    print(f"wrote {path}  ({path.stat().st_size}B)")


def main():
    write("OttDataAnalystAgentStack", agent_stack())
    write("OttDataAnalystApiStack", api_stack())
    write("OttDataAnalystWebStack", web_stack(""))


if __name__ == "__main__":
    main()
