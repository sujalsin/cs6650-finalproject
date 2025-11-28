#!/usr/bin/env python3
"""
Plot Results Script
Creates visualizations from extracted metrics CSV files.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse

# Set style for better-looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10


def load_metrics_data():
    """Load metrics from both local and AWS CSV files."""
    data_files = {
        'local': 'data/metrics_local.csv',
        'aws': 'data/metrics_aws.csv'
    }
    
    dataframes = []
    
    for env, filepath in data_files.items():
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['Environment'] = 'LocalStack' if env == 'local' else 'AWS'
            dataframes.append(df)
            print(f"✓ Loaded {len(df)} records from {filepath}")
        else:
            print(f"⚠ Warning: {filepath} not found, skipping")
    
    if not dataframes:
        raise FileNotFoundError("No metrics CSV files found. Run extract_metrics.py first.")
    
    # Combine dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    print(f"\n✓ Combined dataset: {len(combined_df)} total records")
    return combined_df


def plot_latency_by_environment(df, output_dir):
    """Plot A: Boxplot of Processing Latency by Environment."""
    plt.figure(figsize=(10, 6))
    
    # Create boxplot
    ax = sns.boxplot(
        data=df,
        x='Environment',
        y='processing_latency_ms',
        hue='Environment',
        palette=['#3498db', '#e74c3c'],
        legend=False
    )
    
    plt.title('Processing Latency by Environment', fontsize=14, fontweight='bold')
    plt.xlabel('Environment', fontsize=12)
    plt.ylabel('Processing Latency (ms)', fontsize=12)
    
    # Add mean markers
    for env in df['Environment'].unique():
        mean_val = df[df['Environment'] == env]['processing_latency_ms'].mean()
        plt.axhline(y=mean_val, color='red', linestyle='--', alpha=0.5, linewidth=1)
        plt.text(
            list(df['Environment'].unique()).index(env),
            mean_val,
            f'Mean: {mean_val:.1f}ms',
            ha='center',
            va='bottom',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7)
        )
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'plot_a_latency_by_environment.png')
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_path}")


def plot_file_size_vs_latency(df, output_dir):
    """Plot B: Scatter plot of File Size vs. Latency."""
    plt.figure(figsize=(12, 7))
    
    # Create scatter plot with different colors for each environment
    environments = df['Environment'].unique()
    colors = ['#3498db', '#e74c3c']
    
    for i, env in enumerate(environments):
        env_df = df[df['Environment'] == env]
        plt.scatter(
            env_df['file_size_kb'],
            env_df['processing_latency_ms'],
            label=env,
            alpha=0.6,
            s=50,
            color=colors[i % len(colors)]
        )
    
    # Add trend line
    sns.regplot(
        data=df,
        x='file_size_kb',
        y='processing_latency_ms',
        scatter=False,
        color='green',
        label='Trend Line',
        line_kws={'linestyle': '--', 'linewidth': 2}
    )
    
    plt.title('File Size vs. Processing Latency', fontsize=14, fontweight='bold')
    plt.xlabel('File Size (KB)', fontsize=12)
    plt.ylabel('Processing Latency (ms)', fontsize=12)
    plt.legend(title='Environment', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Add correlation coefficient
    correlation = df['file_size_kb'].corr(df['processing_latency_ms'])
    plt.text(
        0.05, 0.95,
        f'Correlation: {correlation:.3f}',
        transform=plt.gca().transAxes,
        fontsize=11,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'plot_b_file_size_vs_latency.png')
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_path}")


def plot_cold_start_penalty(df, output_dir):
    """Plot C: Bar chart comparing average latency for cold starts vs warm starts."""
    plt.figure(figsize=(10, 6))
    
    # Calculate average latency by cold_start status
    cold_start_stats = df.groupby('cold_start')['processing_latency_ms'].mean()
    
    # Handle case where we might not have both True and False values
    warm_latency = cold_start_stats.get(False, 0)
    cold_latency = cold_start_stats.get(True, 0)
    
    # Prepare data for plotting
    labels = []
    values = []
    colors = []
    
    if False in cold_start_stats.index:
        labels.append('Warm Start')
        values.append(warm_latency)
        colors.append('#2ecc71')
    
    if True in cold_start_stats.index:
        labels.append('Cold Start')
        values.append(cold_latency)
        colors.append('#e74c3c')
    
    if not labels:
        # Fallback if no data
        labels = ['Warm Start', 'Cold Start']
        values = [0, 0]
        colors = ['#2ecc71', '#e74c3c']
    
    # Create bar chart
    bars = plt.bar(
        labels,
        values,
        color=colors,
        alpha=0.8,
        edgecolor='black',
        linewidth=1.5
    )
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        if value > 0:
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 10,
                f'{value:.1f} ms',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )
    
    # Calculate and display penalty if both exist
    if False in cold_start_stats.index and True in cold_start_stats.index:
        penalty = cold_latency - warm_latency
        penalty_pct = (penalty / warm_latency) * 100 if warm_latency > 0 else 0
        
        plt.text(
            0.5, 0.95,
            f'Penalty: +{penalty:.1f}ms ({penalty_pct:.1f}%)',
            transform=plt.gca().transAxes,
            ha='center',
            fontsize=11,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7)
        )
    else:
        plt.text(
            0.5, 0.95,
            'No cold starts detected in this dataset',
            transform=plt.gca().transAxes,
            ha='center',
            fontsize=11,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7)
        )
    
    plt.title('Cold Start Penalty', fontsize=14, fontweight='bold')
    plt.ylabel('Average Processing Latency (ms)', fontsize=12)
    if values:
        plt.ylim(0, max(values) * 1.2 if max(values) > 0 else 100)
    
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'plot_c_cold_start_penalty.png')
    plt.savefig(output_path, bbox_inches='tight')
    plt.close()
    print(f"✓ Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate plots from metrics CSV files')
    parser.add_argument(
        '--output-dir',
        type=str,
        default='plots',
        help='Output directory for plots (default: plots/)'
    )
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("Loading metrics data...")
    df = load_metrics_data()
    
    print(f"\nGenerating plots in '{args.output_dir}' directory...")
    
    # Generate all plots
    plot_latency_by_environment(df, args.output_dir)
    plot_file_size_vs_latency(df, args.output_dir)
    plot_cold_start_penalty(df, args.output_dir)
    
    print(f"\n✓ All plots generated successfully!")


if __name__ == "__main__":
    main()

