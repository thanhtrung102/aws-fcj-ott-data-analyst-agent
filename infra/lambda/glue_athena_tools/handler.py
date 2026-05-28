"""Bedrock Agent action group: Glue catalog + Athena query tools.

Adapted from aws-samples/sample-Agentic-Ai-Data-Operations,
mcp-servers/glue-athena-server/lambda_handler.py -- trimmed to 3 read-only
tools (no create/update/crawler/job) for the OTT data analyst workshop.
"""
import json
import os
import time

import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_REGION", "ap-southeast-1")
RESULTS_BUCKET = os.environ["RESULTS_BUCKET"]
WORKGROUP = os.environ.get("ATHENA_WORKGROUP", "primary")

glue = boto3.client("glue", region_name=REGION)
athena = boto3.client("athena", region_name=REGION)


def _get_tables(database):
    paginator = glue.get_paginator("get_tables")
    tables = []
    for page in paginator.paginate(DatabaseName=database):
        for t in page["TableList"]:
            tables.append({
                "name": t["Name"],
                "type": t.get("TableType", "EXTERNAL_TABLE"),
                "columns": len(t.get("StorageDescriptor", {}).get("Columns", [])),
            })
    return {"database": database, "tables": tables, "count": len(tables)}


def _get_table(database, table):
    resp = glue.get_table(DatabaseName=database, Name=table)
    t = resp["Table"]
    columns = [
        {"name": c["Name"], "type": c["Type"], "comment": c.get("Comment", "")}
        for c in t.get("StorageDescriptor", {}).get("Columns", [])
    ]
    partitions = [
        {"name": c["Name"], "type": c["Type"]} for c in t.get("PartitionKeys", [])
    ]
    return {
        "database": database,
        "table": t["Name"],
        "location": t.get("StorageDescriptor", {}).get("Location", ""),
        "columns": columns,
        "partition_keys": partitions,
    }


def _athena_query(query, database, timeout_seconds=90):
    start = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        ResultConfiguration={"OutputLocation": f"s3://{RESULTS_BUCKET}/results/"},
        WorkGroup=WORKGROUP,
    )
    qid = start["QueryExecutionId"]
    elapsed = 0
    while elapsed < timeout_seconds:
        exec_resp = athena.get_query_execution(QueryExecutionId=qid)
        state = exec_resp["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            stats = exec_resp["QueryExecution"].get("Statistics", {})
            results = athena.get_query_results(QueryExecutionId=qid, MaxResults=50)
            cols = [c["Label"] for c in results["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
            rows = []
            for r in results["ResultSet"]["Rows"][1:]:
                rows.append({cols[i]: r["Data"][i].get("VarCharValue", "") for i in range(len(cols))})
            return {
                "execution_id": qid,
                "columns": cols,
                "rows": rows,
                "row_count": len(rows),
                "data_scanned_bytes": stats.get("DataScannedInBytes", 0),
                "engine_ms": stats.get("EngineExecutionTimeInMillis", 0),
            }
        if state in ("FAILED", "CANCELLED"):
            reason = exec_resp["QueryExecution"]["Status"].get("StateChangeReason", "")
            return {"execution_id": qid, "state": state, "reason": reason}
        time.sleep(1)
        elapsed += 1
    return {"execution_id": qid, "state": "TIMEOUT", "reason": f"Query exceeded {timeout_seconds}s"}


def _params_from_event(event):
    raw = event.get("parameters") or []
    params = {}
    for p in raw:
        name, value, ptype = p.get("name"), p.get("value"), p.get("type", "string")
        if ptype == "integer":
            try:
                value = int(value)
            except (TypeError, ValueError):
                pass
        elif ptype == "boolean":
            value = str(value).lower() in ("true", "1", "yes")
        params[name] = value
    return params


def handler(event, context):
    function = event.get("function") or ""
    params = _params_from_event(event)

    try:
        if function == "get_tables":
            body_obj = _get_tables(params["database"])
        elif function == "get_table":
            body_obj = _get_table(params["database"], params["table"])
        elif function == "athena_query":
            body_obj = _athena_query(
                params["query"], params["database"], int(params.get("timeout_seconds", 90))
            )
        else:
            body_obj = {
                "error": f"unknown function: {function}",
                "available": ["get_tables", "get_table", "athena_query"],
            }
    except ClientError as e:
        body_obj = {"error": str(e), "code": e.response.get("Error", {}).get("Code", "")}
    except KeyError as e:
        body_obj = {"error": f"missing parameter: {e.args[0]}"}

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", "DataAnalystTools"),
            "function": function,
            "functionResponse": {
                "responseBody": {"TEXT": {"body": json.dumps(body_obj, default=str)}}
            },
        },
    }
