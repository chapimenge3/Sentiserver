import os
import json
import base64
import logging
from datetime import datetime
import boto3

logging.basicConfig(level=logging.INFO)

TABLE_NAME = os.environ["TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
comprehend = boto3.client("comprehend")


def update_db(post: dict):
    """Update the post in the database.

    Args:
        post (dict): Post object to be updated in the database

    returns:
        post (dict): Post object that was updated in the database
    """
    updated_at = str(datetime.now())
    update_expression = "SET "
    sentiment_expression = "sentiment = :s"
    status_expression = "#status = :t"
    updated_at_expression = "updated_at = :u"
    sentiment_score_expression = "sentiment_score = :ss"
    update_expression += ", ".join(
        [
            sentiment_expression,
            status_expression,
            updated_at_expression,
            sentiment_score_expression,
        ]
    )
    expression_attribute_values = {
        ":s": post["sentiment"],
        ":t": post["status"],
        ":u": updated_at,
        ":ss": post["sentiment_score"],
    }
    table.update_item(
        Key={"id": post["id"]},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
        ReturnValues="ALL_NEW",
        ExpressionAttributeNames={"#status": "status"},
    )
    return True


def get_sentiment(post):
    """Get the sentiment of the post.

    Args:
        post (dict): Post object to be analyses

    returns:
        post (dict): Post object that was analyses
    """
    response = comprehend.detect_sentiment(Text=post["text"], LanguageCode="en")
    sentiment = response["Sentiment"]
    post["sentiment"] = sentiment
    post["status"] = "processed"
    post["sentiment_score"] = json.dumps(response["SentimentScore"])
    return post


def lambda_handler(event: dict, _):
    """Analyse the post and update the database.

    Args:
        event (dict): Kinesis stream event object
        _ (LambdaContext): AWS Lambda context object

    Returns:
        dict: Kinesis stream response object
    """
    try:
        for record in event["Records"]:
            payload = base64.b64decode(record["kinesis"]["data"])
            post = json.loads(payload)
            post = get_sentiment(post)
            update_db(post)
            logging.info(f'Updated post {post["id"]} in the database.')
        return {"statusCode": 200, "body": json.dumps("Success")}
    except Exception as e:
        logging.error(e)
        logging.info(event)
        return {"statusCode": 500, "body": json.dumps("Error")}
