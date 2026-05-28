from aws_cdk import (
    CfnOutput,
    RemovalPolicy,
    Stack,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
)
from constructs import Construct


class WebStack(Stack):
    """Static SPA on S3 + CloudFront; the agent's API URL is injected as config.js at deploy time."""

    def __init__(self, scope: Construct, cid: str, *, api_url: str, **kwargs) -> None:
        super().__init__(scope, cid, **kwargs)

        web_bucket = s3.Bucket(
            self,
            "WebBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        cdn = cloudfront.Distribution(
            self,
            "WebCdn",
            comment="OTT Data Analyst web app",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(web_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
        )

        s3deploy.BucketDeployment(
            self,
            "DeployWeb",
            sources=[
                s3deploy.Source.asset("web"),
                s3deploy.Source.data("config.js", f'window.API_URL = "{api_url}";'),
            ],
            destination_bucket=web_bucket,
            distribution=cdn,
            distribution_paths=["/*"],
        )

        CfnOutput(self, "WebUrl", value=f"https://{cdn.distribution_domain_name}")
