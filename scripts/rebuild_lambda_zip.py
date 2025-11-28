#!/usr/bin/env python3
"""Rebuild Lambda zip with proper permissions for LocalStack."""

import os
import zipfile
import subprocess
import shutil

def rebuild_zip():
    """Rebuild the Lambda deployment package."""
    print("Cleaning up...")
    if os.path.exists('package'):
        shutil.rmtree('package')
    if os.path.exists('function.zip'):
        os.remove('function.zip')
    
    os.makedirs('package', exist_ok=True)
    
    print("Installing Pillow...")
    subprocess.run([
        'pip', 'install',
        '--platform', 'manylinux2014_x86_64',
        '--target=package',
        '--implementation', 'cp',
        '--python-version', '3.9',
        '--only-binary=:all:',
        '--upgrade',
        'Pillow'
    ], check=True, capture_output=True)
    
    print("Copying Lambda function...")
    shutil.copy('src/lambda_function.py', 'package/lambda_function.py')
    
    print("Creating zip file with proper permissions...")
    with zipfile.ZipFile('function.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('package'):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, 'package')
                # Add file with explicit permissions
                zipf.write(file_path, arc_name)
                # Set permissions: 644 for files, 755 for directories
                info = zipf.getinfo(arc_name)
                info.external_attr = 0o644 << 16  # -rw-r--r--
    
    print("✓ Created function.zip")
    print(f"  Size: {os.path.getsize('function.zip') / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    rebuild_zip()

