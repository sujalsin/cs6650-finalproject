#!/usr/bin/env python3
"""
Helper script to manually trigger Lambda for S3 objects.
This works around LocalStack's S3 notification limitations.
"""

import boto3
import sys
import json
from tqdm import tqdm

def trigger_lambda_for_objects(env, bucket_name, prefix="load_test"):
    """Trigger Lambda function for all objects with given prefix."""
    # Configure clients
    config = {}
    if env == "local":
        config['endpoint_url'] = 'http://localhost:4566'
        config['aws_access_key_id'] = 'test'
        config['aws_secret_access_key'] = 'test'
    
    s3_client = boto3.client('s3', **config)
    lambda_client = boto3.client('lambda', **config)
    
    # List all objects
    print(f"Listing objects in bucket: {bucket_name}")
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
    
    objects = []
    for page in pages:
        if 'Contents' in page:
            objects.extend([obj['Key'] for obj in page['Contents']])
    
    print(f"Found {len(objects)} objects to process")
    
    # Trigger Lambda for each object
    function_name = "order-processing-part2-image-processor"
    success_count = 0
    error_count = 0
    
    with tqdm(total=len(objects), desc="Triggering Lambda", unit="image") as pbar:
        for obj_key in objects:
            try:
                # Create S3 event
                event = {
                    "Records": [
                        {
                            "eventVersion": "2.1",
                            "eventSource": "aws:s3",
                            "s3": {
                                "bucket": {
                                    "name": bucket_name
                                },
                                "object": {
                                    "key": obj_key
                                }
                            }
                        }
                    ]
                }
                
                # Invoke Lambda
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType='RequestResponse',
                    Payload=json.dumps(event)
                )
                
                # Check response
                response_payload = json.loads(response['Payload'].read())
                if 'FunctionError' not in response:
                    success_count += 1
                else:
                    error_count += 1
                    print(f"\nError processing {obj_key}: {response_payload.get('errorMessage', 'Unknown error')}")
                
                pbar.update(1)
                
                # Small delay to avoid overwhelming LocalStack
                import time
                time.sleep(0.1)
                
            except Exception as e:
                error_count += 1
                print(f"\nError processing {obj_key}: {e}")
                pbar.update(1)
    
    print(f"\n✓ Successfully processed: {success_count}/{len(objects)}")
    if error_count > 0:
        print(f"⚠ Errors: {error_count}/{len(objects)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Trigger Lambda for S3 objects')
    parser.add_argument('--env', choices=['local', 'aws'], required=True, help='Environment')
    parser.add_argument('--bucket', type=str, default='order-processing-part2-image-processing', help='S3 bucket name')
    parser.add_argument('--prefix', type=str, default='load_test', help='Object key prefix')
    
    args = parser.parse_args()
    trigger_lambda_for_objects(args.env, args.bucket, args.prefix)


