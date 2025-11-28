#!/usr/bin/env python3
"""
Metrics Extraction Script
Extracts metrics from DynamoDB and saves to CSV for analysis.
"""

import argparse
import os
import boto3
import pandas as pd
from decimal import Decimal
import json
import subprocess

# Default table name (can be overridden by Terraform outputs)
DEFAULT_TABLE = "order-processing-part2-image-results"


def get_table_name_from_terraform(env):
    """Try to get table name from Terraform outputs."""
    try:
        if env == "local":
            cmd = ["tflocal", "output", "-json", "image_processor_dynamodb_table_name"]
        else:
            cmd = ["terraform", "output", "-json", "image_processor_dynamodb_table_name"]
        
        result = subprocess.run(
            cmd,
            cwd="terraform",
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            output = json.loads(result.stdout.strip())
            return output.get("value", DEFAULT_TABLE)
    except Exception as e:
        print(f"Warning: Could not read Terraform output, using default: {e}")
    
    return DEFAULT_TABLE


def decimal_to_float(obj):
    """Convert Decimal to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def scan_dynamodb_table(env, table_name):
    """Scan DynamoDB table and return all items."""
    # Configure DynamoDB client
    dynamodb_config = {}
    if env == "local":
        dynamodb_config['endpoint_url'] = 'http://localhost:4566'
        dynamodb_config['aws_access_key_id'] = 'test'
        dynamodb_config['aws_secret_access_key'] = 'test'
    
    dynamodb = boto3.resource('dynamodb', **dynamodb_config)
    table = dynamodb.Table(table_name)
    
    print(f"Scanning DynamoDB table: {table_name}")
    print(f"Environment: {env.upper()}")
    
    items = []
    last_evaluated_key = None
    
    # Scan with pagination
    while True:
        scan_kwargs = {}
        if last_evaluated_key:
            scan_kwargs['ExclusiveStartKey'] = last_evaluated_key
        
        response = table.scan(**scan_kwargs)
        items.extend(response.get('Items', []))
        
        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break
    
    print(f"Found {len(items)} records")
    return items


def transform_to_dataframe(items):
    """Convert DynamoDB items to pandas DataFrame with required columns."""
    if not items:
        print("Warning: No items found in DynamoDB table")
        return pd.DataFrame(columns=['filename', 'file_size_kb', 'processing_latency_ms', 'cold_start', 'simulated_class'])
    
    from decimal import Decimal
    
    records = []
    for item in items:
        # Handle Decimal types from DynamoDB
        file_size = item.get('file_size', 0)
        if isinstance(file_size, Decimal):
            file_size = float(file_size)
        elif not isinstance(file_size, (int, float)):
            file_size = 0
        
        processing_latency = item.get('processing_latency', 0)
        if isinstance(processing_latency, Decimal):
            processing_latency = float(processing_latency)
        elif not isinstance(processing_latency, (int, float)):
            processing_latency = 0
        
        record = {
            'filename': item.get('filename', ''),
            'file_size_kb': round(file_size / 1024.0, 2),
            'processing_latency_ms': float(processing_latency),
            'cold_start': bool(item.get('is_cold_start', False)),
            'simulated_class': item.get('simulated_classification', 'Unknown')
        }
        records.append(record)
    
    df = pd.DataFrame(records)
    return df


def save_metrics(df, env):
    """Save metrics DataFrame to CSV file."""
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    output_file = f'data/metrics_{env}.csv'
    df.to_csv(output_file, index=False)
    
    print(f"\n✓ Metrics saved to: {output_file}")
    print(f"  Total records: {len(df)}")
    print(f"  Columns: {', '.join(df.columns.tolist())}")
    
    # Print summary statistics
    if len(df) > 0:
        print(f"\nSummary Statistics:")
        print(f"  Average latency: {df['processing_latency_ms'].mean():.2f} ms")
        print(f"  Average file size: {df['file_size_kb'].mean():.2f} KB")
        print(f"  Cold starts: {df['cold_start'].sum()} ({df['cold_start'].sum()/len(df)*100:.1f}%)")
        print(f"  Classifications: {df['simulated_class'].value_counts().to_dict()}")


def main():
    parser = argparse.ArgumentParser(description='Extract metrics from DynamoDB to CSV')
    parser.add_argument(
        '--env',
        choices=['local', 'aws'],
        required=True,
        help='Environment: local (LocalStack) or aws (AWS)'
    )
    parser.add_argument(
        '--table',
        type=str,
        default=None,
        help='DynamoDB table name (default: read from Terraform outputs)'
    )
    
    args = parser.parse_args()
    
    # Get table name
    if args.table:
        table_name = args.table
    else:
        table_name = get_table_name_from_terraform(args.env)
    
    print(f"Using DynamoDB table: {table_name}")
    
    # Scan table
    items = scan_dynamodb_table(args.env, table_name)
    
    # Transform to DataFrame
    df = transform_to_dataframe(items)
    
    # Save to CSV
    save_metrics(df, args.env)


if __name__ == "__main__":
    main()

