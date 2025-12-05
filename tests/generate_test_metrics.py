#!/usr/bin/env python3
"""
Generate test metrics data for visualization testing.
This creates realistic sample data based on the Lambda function's behavior.
"""

import pandas as pd
import random
import os

def generate_test_metrics():
    """Generate realistic test metrics data."""
    records = []
    
    # Generate 50 records matching the load test pattern
    # 20 small (~100KB), 20 medium (~1MB), 10 large (~5MB)
    
    sizes = (
        [100] * 20 +  # Small images ~100KB
        [1000] * 20 +  # Medium images ~1MB
        [5000] * 10    # Large images ~5MB
    )
    
    categories = (
        ['small'] * 20 +
        ['medium'] * 20 +
        ['large'] * 10
    )
    
    # Simulate the Lambda's complexity-based latency
    # Base latency: 200ms - 2000ms based on file size
    # 5% chance of long tail (+1000ms)
    # Cold start adds some overhead
    
    cold_start_count = 0
    for i, (size_kb, category) in enumerate(zip(sizes, categories)):
        # First few are cold starts
        is_cold_start = (cold_start_count < 3)
        if is_cold_start:
            cold_start_count += 1
        
        # Calculate base latency based on complexity (file size)
        complexity = min(size_kb / 10000, 1.0)  # Normalize to 0-1
        base_latency = 200 + (complexity * 1800)  # 200ms to 2000ms
        
        # 5% chance of long tail delay
        if random.random() < 0.05:
            base_latency += 1000
        
        # Cold start adds ~50-100ms overhead
        if is_cold_start:
            base_latency += random.uniform(50, 100)
        
        # Add some random variation
        latency = base_latency + random.uniform(-50, 50)
        latency = max(200, latency)  # Minimum 200ms
        
        # Random classification
        classification = random.choice(["Document", "Receipt", "Photo"])
        
        records.append({
            'filename': f'load_test_{category}_{i+1:03d}.png',
            'file_size_kb': round(size_kb + random.uniform(-10, 10), 2),
            'processing_latency_ms': round(latency, 2),
            'cold_start': is_cold_start,
            'simulated_class': classification
        })
    
    df = pd.DataFrame(records)
    return df

def main():
    os.makedirs('data', exist_ok=True)
    
    print("Generating test metrics data...")
    df = generate_test_metrics()
    
    output_file = 'data/metrics_local.csv'
    df.to_csv(output_file, index=False)
    
    print(f"✓ Generated {len(df)} test records")
    print(f"✓ Saved to: {output_file}")
    print(f"\nSummary Statistics:")
    print(f"  Average latency: {df['processing_latency_ms'].mean():.2f} ms")
    print(f"  Average file size: {df['file_size_kb'].mean():.2f} KB")
    print(f"  Cold starts: {df['cold_start'].sum()} ({df['cold_start'].sum()/len(df)*100:.1f}%)")
    print(f"  Classifications: {df['simulated_class'].value_counts().to_dict()}")

if __name__ == "__main__":
    main()


