import json
import os
import time
import random
import urllib.parse
import boto3
from PIL import Image
from io import BytesIO

# Global variable to detect cold starts
_is_warm = False

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get table name from environment variable
TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME', 'image-processing-results')


def lambda_handler(event, context):
    """
    Handle S3 Object Created events.
    Processes images and writes results to DynamoDB.
    """
    global _is_warm
    
    # Detect cold start
    is_cold_start = not _is_warm
    _is_warm = True
    
    # Log cold start if applicable
    if is_cold_start:
        print("Cold start detected: true")
    
    try:
        # Extract S3 event information
        for record in event.get('Records', []):
            bucket_name = record['s3']['bucket']['name']
            # URL decode the object key in case it's encoded
            object_key = urllib.parse.unquote_plus(record['s3']['object']['key'])
            
            # Download image from S3
            print(f"Processing image: s3://{bucket_name}/{object_key}")
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            image_data = response['Body'].read()
            file_size = len(image_data)
            
            # Extract metadata using Pillow
            image = Image.open(BytesIO(image_data))
            width, height = image.size
            image_format = image.format or 'Unknown'
            
            print(f"Image metadata - Size: {file_size} bytes, Dimensions: {width}x{height}, Format: {image_format}")
            
            # Calculate complexity score based on file size
            # Normalize to a score between 0 and 1
            complexity_score = min(file_size / (10 * 1024 * 1024), 1.0)  # Max at 10MB
            
            # Simulate processing latency (200ms - 2000ms based on complexity)
            base_latency = 200 + (complexity_score * 1800)  # 200ms to 2000ms
            processing_latency_ms = base_latency
            
            # 5% chance of long tail delay (extra 1 second)
            if random.random() < 0.05:
                processing_latency_ms += 1000
                print("Long tail delay triggered (+1000ms)")
            
            # Simulate the processing time
            time.sleep(processing_latency_ms / 1000.0)
            
            # Simulate classification (random choice)
            classification = random.choice(["Document", "Receipt", "Photo"])
            
            # Prepare DynamoDB record
            # DynamoDB doesn't support float, so convert to Decimal or use int for latency
            from decimal import Decimal
            record_data = {
                'filename': object_key,
                'file_size': file_size,
                'processing_latency': Decimal(str(round(processing_latency_ms, 2))),
                'is_cold_start': is_cold_start,
                'simulated_classification': classification,
                'width': width,
                'height': height,
                'format': image_format,
                'timestamp': int(time.time())
            }
            
            # Write to DynamoDB
            table = dynamodb.Table(TABLE_NAME)
            table.put_item(Item=record_data)
            
            print(f"Successfully processed and stored: {object_key}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Image processed successfully',
                    'filename': object_key,
                    'classification': classification,
                    'is_cold_start': is_cold_start
                })
            }
    
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise e

