import json
import logging
import os
from datetime import datetime
from uuid import uuid4 as uuid

import boto3

logging.basicConfig(level=logging.INFO)

TABLE_NAME = os.environ["TABLE_NAME"]
STREAM_NAME = os.environ["STREAM_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
stream = boto3.client("kinesis")

# Please edit the below if you want to restrict the origin of the request
headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": True,
}


def add_to_db(post):
    """Add the post to the database.

    Args:
        post (dict): Post object to be added to the database
    """
    table.put_item(Item=post)
    return True


def add_to_stream(post: dict):
    """Add the post to the stream.

    Args:
        post (dict): Post object to be added to the stream
    """
    stream.put_record(StreamName=STREAM_NAME, Data=json.dumps(post), PartitionKey="1")
    return True


def lambda_handler(event, _):
    """Feed the data to the stream and dynamodb to be processed by the worker.

    Args:
        event (dict): API Gateway request object
        _ (LambdaContext): AWS Lambda context object

    Returns:
        dict: API Gateway response object
    """

    try:
        body = event["body"]
        if not body:
            return {"statusCode": 400, "headers": headers, "body": "No data provided"}
        if isinstance(body, str):
            body = json.loads(body)

        text = body.get("text")
        if not text:
            return {"statusCode": 400, "headers": headers, "body": "No text provided"}

        post = {
            "id": str(uuid()),
            "text": text,
            "status": "pending",
            "timestamp": str(datetime.now()),
            "updated_at": str(datetime.now()),
            "sentiment": None,
            "sentiment_score": None,
        }

        add_to_db(post)
        add_to_stream(post)

        return {"statusCode": 200, "headers": headers, "body": json.dumps(post)}

    except Exception as e:
        logging.error(e)
        logging.info(event)
        return {"statusCode": 500, "headers": headers, "body": "Internal Server Error"}
