import os
import json
import logging
import boto3

logging.basicConfig(level=logging.INFO)

TABLE_NAME = os.environ["TABLE_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# Please edit the below if you want to restrict the origin of the request
headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Credentials": True,
}


def get_post(post_id):
    """Get the post from the database.

    Args:
        post_id (str): ID of the post to be retrieved from the database

    Returns:
        post (dict): Post object that was retrieved from the database
    """
    response = table.get_item(Key={"id": post_id})
    return response["Item"] if "Item" in response else None


def lambda_handler(event, _):
    """Get the post from the database.

    Args:
        event (dict): API Gateway request object

    Returns:
        dict: API Gateway response object
    """
    try:
        query_parameters = event.get("queryStringParameters")
        if not query_parameters:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"message": "Missing path parameters"}),
            }

        post_id = query_parameters.get("id")
        if not post_id:
            return {
                "statusCode": 400,
                "headers": headers,
                "body": json.dumps({"message": "Missing post ID"}),
            }

        post = get_post(post_id)
        if not post:
            return {
                "statusCode": 404,
                "headers": headers,
                "body": json.dumps({"message": "Post not found"}),
            }

        return {"statusCode": 200, "headers": headers, "body": json.dumps(post)}
    except Exception as e:
        logging.error(e)
        print(event)
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({"message": "Internal server error"}),
        }
