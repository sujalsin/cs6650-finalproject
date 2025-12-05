#!/usr/bin/env python3
"""
Load Generator Script
Generates random images and uploads them to S3 to trigger Lambda processing.
"""

import argparse
import os
import random
import boto3
from PIL import Image
import numpy as np
from tqdm import tqdm
import json
import subprocess

# Default bucket name (can be overridden by Terraform outputs)
DEFAULT_BUCKET = "order-processing-part2-image-processing"


def get_bucket_name_from_terraform(env):
    """Try to get bucket name from Terraform outputs."""
    try:
        if env == "local":
            cmd = ["tflocal", "output", "-json", "image_processor_s3_bucket_name"]
        else:
            cmd = ["terraform", "output", "-json", "image_processor_s3_bucket_name"]
        
        result = subprocess.run(
            cmd,
            cwd="terraform",
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            output = json.loads(result.stdout.strip())
            return output.get("value", DEFAULT_BUCKET)
    except Exception as e:
        print(f"Warning: Could not read Terraform output, using default: {e}")
    
    return DEFAULT_BUCKET


def generate_image(target_size_kb, filename):
    """
    Generate a random RGB noise image that approximates the target size.
    Uses compression to get closer to target size.
    """
    # Start with a reasonable dimension estimate
    # PNG compression varies, so we'll iterate to get close to target
    target_bytes = target_size_kb * 1024
    
    # Rough estimate: uncompressed RGB is width * height * 3 bytes
    # PNG compression typically gives 50-80% reduction for noise
    # Start with estimate and adjust
    if target_size_kb < 200:  # Small: ~100KB
        base_size = 200
    elif target_size_kb < 1200:  # Medium: ~1MB
        base_size = 600
    else:  # Large: ~5MB
        base_size = 1200
    
    # Generate random RGB noise
    img_array = np.random.randint(0, 256, (base_size, base_size, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, 'RGB')
    
    # Save with compression and check size
    temp_path = f"/tmp/{filename}"
    img.save(temp_path, 'PNG', optimize=True, compress_level=9)
    
    actual_size = os.path.getsize(temp_path)
    
    # If too small, increase dimensions; if too large, decrease
    attempts = 0
    while abs(actual_size - target_bytes) > target_bytes * 0.2 and attempts < 5:
        if actual_size < target_bytes:
            # Increase size
            base_size = int(base_size * 1.2)
        else:
            # Decrease size
            base_size = int(base_size * 0.9)
        
        img_array = np.random.randint(0, 256, (base_size, base_size, 3), dtype=np.uint8)
        img = Image.fromarray(img_array, 'RGB')
        img.save(temp_path, 'PNG', optimize=True, compress_level=9)
        actual_size = os.path.getsize(temp_path)
        attempts += 1
    
    return temp_path


def upload_images(env, bucket_name):
    """Generate and upload images to S3."""
    # Configure S3 client
    s3_config = {}
    if env == "local":
        s3_config['endpoint_url'] = 'http://localhost:4566'
        s3_config['aws_access_key_id'] = 'test'
        s3_config['aws_secret_access_key'] = 'test'
    
    s3_client = boto3.client('s3', **s3_config)
    
    # Verify bucket exists
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception as e:
        print(f"Error: Bucket '{bucket_name}' not accessible: {e}")
        return
    
    # Image generation plan
    images_to_generate = [
        (20, 100, "small"),   # 20 small images ~100KB
        (20, 1000, "medium"), # 20 medium images ~1MB
        (10, 5000, "large"),   # 10 large images ~5MB
    ]
    
    total_images = sum(count for count, _, _ in images_to_generate)
    uploaded = 0
    
    print(f"Generating and uploading {total_images} images to bucket: {bucket_name}")
    print(f"Environment: {env.upper()}")
    
    with tqdm(total=total_images, desc="Uploading images", unit="image") as pbar:
        for count, size_kb, category in images_to_generate:
            for i in range(count):
                filename = f"load_test_{category}_{i+1:03d}.png"
                temp_path = None
                
                try:
                    # Generate image
                    temp_path = generate_image(size_kb, filename)
                    
                    # Upload to S3
                    s3_client.upload_file(
                        temp_path,
                        bucket_name,
                        filename,
                        ExtraArgs={'ContentType': 'image/png'}
                    )
                    
                    uploaded += 1
                    pbar.update(1)
                    
                except Exception as e:
                    print(f"\nError uploading {filename}: {e}")
                    pbar.update(1)
                finally:
                    # Clean up temp file
                    if temp_path and os.path.exists(temp_path):
                        os.remove(temp_path)
    
    print(f"\n Successfully uploaded {uploaded}/{total_images} images")
    print(f" Images are being processed by Lambda function")
    print(f" Wait a few minutes, then run extract_metrics.py to collect results")


def main():
    parser = argparse.ArgumentParser(description='Generate load by uploading images to S3')
    parser.add_argument(
        '--env',
        choices=['local', 'aws'],
        required=True,
        help='Environment: local (LocalStack) or aws (AWS)'
    )
    parser.add_argument(
        '--bucket',
        type=str,
        default=None,
        help='S3 bucket name (default: read from Terraform outputs)'
    )
    
    args = parser.parse_args()
    
    # Get bucket name
    if args.bucket:
        bucket_name = args.bucket
    else:
        bucket_name = get_bucket_name_from_terraform(args.env)
    
    print(f"Using S3 bucket: {bucket_name}")
    upload_images(args.env, bucket_name)


if __name__ == "__main__":
    main()


