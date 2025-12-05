#!/usr/bin/env python3
"""
Plot Results Script
Creates visualizations from extracted metrics CSV files.
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

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
    plt.figure(figsize=(12, 7))
    
    # Create boxplot
    ax = sns.boxplot(
        data=df,
        x='Environment',
        y='processing_latency_ms',
        hue='Environment',
        palette=['#3498db', '#e74c3c'],
        legend=False,
        showfliers=True  # Explicitly show outliers
    )
    
    # Manually plot outliers with different colors and sizes for each environment
    environments = df['Environment'].unique()
    colors = ['#3498db', '#e74c3c']
    markers = ['o', 's']  # Circle for LocalStack, Square for AWS
    
    for i, env in enumerate(environments):
        env_df = df[df['Environment'] == env]
        
        # Calculate IQR to identify outliers
        Q1 = env_df['processing_latency_ms'].quantile(0.25)
        Q3 = env_df['processing_latency_ms'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Get outliers
        outliers = env_df[
            (env_df['processing_latency_ms'] < lower_bound) | 
            (env_df['processing_latency_ms'] > upper_bound)
        ]
        
        # Plot outliers with distinct styling
        if len(outliers) > 0:
            x_pos = i  # Position on x-axis
            plt.scatter(
                [x_pos] * len(outliers),
                outliers['processing_latency_ms'],
                color=colors[i],
                marker=markers[i],
                s=100,  # Larger size
                alpha=0.7,
                edgecolors='black',
                linewidths=1.5,
                label=f'{env} Outliers' if i == 0 else None,
                zorder=10  # Draw on top
            )
            
            # Add count annotation
            if len(outliers) > 0:
                max_outlier = outliers['processing_latency_ms'].max()
                plt.text(
                    x_pos,
                    max_outlier + 50,
                    f'{len(outliers)} outliers',
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8)
                )
    
    plt.title('Processing Latency by Environment', fontsize=14, fontweight='bold')
    plt.xlabel('Environment', fontsize=12)
    plt.ylabel('Processing Latency (ms)', fontsize=12)
    
    # Add mean markers
    for i, env in enumerate(environments):
        mean_val = df[df['Environment'] == env]['processing_latency_ms'].mean()
        plt.axhline(y=mean_val, color='red', linestyle='--', alpha=0.5, linewidth=1)
        plt.text(
            i,
            mean_val,
            f'Mean: {mean_val:.1f}ms',
            ha='center',
            va='bottom',
            fontsize=9,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7)
        )
    
    # Add statistics text box
    stats_text = []
    for env in environments:
        env_df = df[df['Environment'] == env]
        stats_text.append(
            f"{env}:\n"
            f"  Median: {env_df['processing_latency_ms'].median():.1f}ms\n"
            f"  Mean: {env_df['processing_latency_ms'].mean():.1f}ms\n"
            f"  Std: {env_df['processing_latency_ms'].std():.1f}ms"
        )
    
    plt.text(
        0.98, 0.02,
        '\n'.join(stats_text),
        transform=plt.gca().transAxes,
        fontsize=9,
        verticalalignment='bottom',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
        family='monospace'
    )
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'plot_a_latency_by_environment.png')
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Saved: {output_path}")


def plot_file_size_vs_latency(df, output_dir):
    """Plot B: Scatter plot of File Size vs. Latency."""
    plt.figure(figsize=(12, 7))
    
    # Create scatter plot with different colors for each environment
    # Add jitter to make overlapping points visible
    environments = df['Environment'].unique()
    colors = ['#3498db', '#e74c3c']
    markers = ['o', 's']  # Circle for LocalStack, Square for AWS
    
    for i, env in enumerate(environments):
        env_df = df[df['Environment'] == env].copy()
        
        # Add small random jitter to file_size to separate overlapping points
        # Jitter is 1% of the data range
        file_size_range = env_df['file_size_kb'].max() - env_df['file_size_kb'].min()
        jitter_amount = file_size_range * 0.01
        np.random.seed(42 + i)  # Consistent jitter for reproducibility
        env_df['file_size_kb_jittered'] = env_df['file_size_kb'] + np.random.normal(0, jitter_amount, len(env_df))
        
        # Plot with jittered x-values
        scatter = plt.scatter(
            env_df['file_size_kb_jittered'],
            env_df['processing_latency_ms'],
            label=env,
            alpha=0.6,
            s=60,
            color=colors[i % len(colors)],
            marker=markers[i],
            edgecolors='black',
            linewidths=0.5
        )
        
        # Add count annotations for clusters
        # Group by approximate file size clusters
        for size_cluster in [117.54, 1056.75, 4225.87]:
            cluster_data = env_df[
                (env_df['file_size_kb'] >= size_cluster - 1) & 
                (env_df['file_size_kb'] <= size_cluster + 1)
            ]
            if len(cluster_data) > 1:
                avg_latency = cluster_data['processing_latency_ms'].mean()
                plt.text(
                    size_cluster,
                    avg_latency + 50,
                    f'n={len(cluster_data)}',
                    ha='center',
                    va='bottom',
                    fontsize=8,
                    color=colors[i % len(colors)],
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7, edgecolor=colors[i % len(colors)])
                )
    
    # Add trend line with confidence interval (the green shaded region)
    # ci=95 means 95% confidence interval
    sns.regplot(
        data=df,
        x='file_size_kb',
        y='processing_latency_ms',
        scatter=False,
        color='green',
        label='Trend Line (95% CI)',
        ci=95,  # 95% confidence interval (the green shaded region)
        line_kws={'linestyle': '--', 'linewidth': 2},
        scatter_kws={'alpha': 0}  # Don't plot points again
    )
    
    plt.title('File Size vs. Processing Latency', fontsize=14, fontweight='bold')
    plt.xlabel('File Size (KB)', fontsize=12)
    plt.ylabel('Processing Latency (ms)', fontsize=12)
    plt.legend(title='Environment', fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Add correlation coefficient and explanation
    correlation = df['file_size_kb'].corr(df['processing_latency_ms'])
    explanation_text = (
        f'Correlation: {correlation:.3f}\n'
        f'Green shaded area = 95% confidence interval\n'
        f'Points jittered slightly to show overlap'
    )
    plt.text(
        0.05, 0.95,
        explanation_text,
        transform=plt.gca().transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7)
    )
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'plot_b_file_size_vs_latency.png')
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Saved: {output_path}")


def plot_cold_start_penalty_overall(df, output_dir):
    """Plot C: Overall comparison of Cold Start vs Warm Start across all data."""
    plt.figure(figsize=(10, 6))
    
    # Calculate average latency by cold_start status
    cold_start_stats = df.groupby('cold_start')['processing_latency_ms'].agg(['mean', 'std', 'count']).reset_index()
    
    # Prepare data for plotting
    labels = []
    means = []
    stds = []
    counts = []
    colors = []
    
    for _, row in cold_start_stats.iterrows():
        is_cold = row['cold_start']
        if is_cold:
            labels.append('Cold Start')
            colors.append('#e74c3c')
        else:
            labels.append('Warm Start')
            colors.append('#2ecc71')
        means.append(row['mean'])
        stds.append(row['std'])
        counts.append(int(row['count']))
    
    # Create bar chart with error bars
    bars = plt.bar(
        labels,
        means,
        color=colors,
        alpha=0.8,
        edgecolor='black',
        linewidth=1.5,
        yerr=stds,
        capsize=10,
        error_kw={'elinewidth': 2, 'capthick': 2}
    )
    
    # Add value labels
    for bar, mean_val, std_val, count in zip(bars, means, stds, counts):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + std_val + 30,
            f'Mean: {mean_val:.1f} ms\nStd: ±{std_val:.1f} ms\nn={count}',
            ha='center',
            va='bottom',
            fontsize=10,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
        )
    
    # Calculate and display penalty if both exist
    if len(means) == 2:
        warm_mean = means[1] if labels[0] == 'Cold Start' else means[0]
        cold_mean = means[0] if labels[0] == 'Cold Start' else means[1]
        penalty = cold_mean - warm_mean
        penalty_pct = (penalty / warm_mean) * 100 if warm_mean > 0 else 0
        
        penalty_text = f'Cold Start Penalty: +{penalty:.1f}ms ({penalty_pct:+.1f}%)'
        plt.text(
            0.5, 0.95,
            penalty_text,
            transform=plt.gca().transAxes,
            ha='center',
            fontsize=11,
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8),
            verticalalignment='top'
        )
    
    plt.title('Cold Start Penalty: Overall Comparison', fontsize=14, fontweight='bold')
    plt.ylabel('Average Processing Latency (ms)', fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    if means:
        plt.ylim(0, max(means) + max(stds) + 100)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, 'plot_c_cold_start_penalty.png')
    plt.savefig(output_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Saved: {output_path}")


def plot_cold_start_penalty(df, output_dir):
    """Plot C: Two separate plots comparing LocalStack vs AWS for cold start files and warm start files."""
    
    # Separate LocalStack and AWS data
    localstack_df = df[df['Environment'] == 'LocalStack'].copy()
    aws_df = df[df['Environment'] == 'AWS'].copy()
    
    # Identify files that were cold starts in AWS
    aws_cold_start_files = set(aws_df[aws_df['cold_start'] == True]['filename'].values)
    aws_warm_start_files = set(aws_df[aws_df['cold_start'] == False]['filename'].values)
    
    # Get corresponding LocalStack data for these files
    localstack_cold_start_files = localstack_df[localstack_df['filename'].isin(aws_cold_start_files)]
    aws_cold_start_files_data = aws_df[aws_df['filename'].isin(aws_cold_start_files)]
    
    localstack_warm_start_files = localstack_df[localstack_df['filename'].isin(aws_warm_start_files)]
    aws_warm_start_files_data = aws_df[aws_df['filename'].isin(aws_warm_start_files)]
    
    # ===== PLOT C1: Cold Start Files (LocalStack Warm vs AWS Cold) =====
    fig1, ax1 = plt.subplots(1, 1, figsize=(10, 6))
    
    if len(localstack_cold_start_files) > 0 and len(aws_cold_start_files_data) > 0:
        localstack_mean = localstack_cold_start_files['processing_latency_ms'].mean()
        aws_mean = aws_cold_start_files_data['processing_latency_ms'].mean()
        localstack_median = localstack_cold_start_files['processing_latency_ms'].median()
        aws_median = aws_cold_start_files_data['processing_latency_ms'].median()
        localstack_std = localstack_cold_start_files['processing_latency_ms'].std()
        aws_std = aws_cold_start_files_data['processing_latency_ms'].std()
        
        labels = ['LocalStack\n(Warm Start)', 'AWS\n(Cold Start)']
        means = [localstack_mean, aws_mean]
        medians = [localstack_median, aws_median]
        stds = [localstack_std, aws_std]
        colors = ['#3498db', '#e74c3c']
        counts = [len(localstack_cold_start_files), len(aws_cold_start_files_data)]
        
        bars = ax1.bar(
            labels,
            means,
            color=colors,
            alpha=0.8,
            edgecolor='black',
            linewidth=1.5,
            yerr=stds,
            capsize=10,
            error_kw={'elinewidth': 2, 'capthick': 2}
        )
        
        # Add median markers
        for i, (bar, median_val) in enumerate(zip(bars, medians)):
            ax1.plot([bar.get_x(), bar.get_x() + bar.get_width()], 
                    [median_val, median_val], 
                    'k--', linewidth=2, label='Median' if i == 0 else '')
        
        # Add value labels with both mean and median
        for bar, mean_val, median_val, std_val, count in zip(bars, means, medians, stds, counts):
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + std_val + 50,
                f'Mean: {mean_val:.1f} ms\nMedian: {median_val:.1f} ms\nStd: ±{std_val:.1f} ms\nn={count}',
                ha='center',
                va='bottom',
                fontsize=9,
                fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8)
            )
        
        # Check for outliers (long-tail delays)
        localstack_outliers = localstack_cold_start_files[localstack_cold_start_files['processing_latency_ms'] > 1000]
        has_outlier = len(localstack_outliers) > 0
        
        # Calculate penalty using median (more robust to outliers)
        penalty_median = aws_median - localstack_median
        penalty_mean = aws_mean - localstack_mean
        
        if has_outlier:
            outlier_info = f'Outlier detected: {len(localstack_outliers)} file(s) with long-tail delay'
            penalty_text = (
                f'Using Median (robust): Cold Start Penalty = {penalty_median:+.1f}ms\n'
                f'Using Mean (affected by outlier): {penalty_mean:+.1f}ms\n'
                f'{outlier_info}'
            )
            bbox_color = 'yellow'
        else:
            penalty_text = f'Cold Start Penalty: {penalty_mean:+.1f}ms (mean) / {penalty_median:+.1f}ms (median)'
            bbox_color = 'lightblue'
        
        ax1.text(
            0.5, 0.95,
            penalty_text,
            transform=ax1.transAxes,
            ha='center',
            fontsize=10,
            bbox=dict(boxstyle='round', facecolor=bbox_color, alpha=0.8),
            verticalalignment='top'
        )
        
        ax1.set_ylabel('Average Processing Latency (ms)', fontsize=12)
        ax1.set_title(f'Cold Start Files: LocalStack (Warm) vs AWS (Cold)\n{len(aws_cold_start_files)} files', 
                      fontsize=13, fontweight='bold')
        ax1.legend(['Median'], loc='upper right', fontsize=9)
        ax1.grid(True, alpha=0.3, axis='y')
        # Increase y-limit to accommodate text boxes
        max_height = max(means) + max(stds) + 200
        if has_outlier:
            max_height = max(max_height, localstack_outliers['processing_latency_ms'].max() + 100)
        ax1.set_ylim(0, max_height)
    
    plt.tight_layout()
    output_path1 = os.path.join(output_dir, 'plot_c1_cold_start_files.png')
    plt.savefig(output_path1, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Saved: {output_path1}")
    
    # ===== PLOT C2: Warm Start Files (LocalStack Warm vs AWS Warm) =====
    fig2, ax2 = plt.subplots(1, 1, figsize=(10, 6))
    
    if len(localstack_warm_start_files) > 0 and len(aws_warm_start_files_data) > 0:
        localstack_mean = localstack_warm_start_files['processing_latency_ms'].mean()
        aws_mean = aws_warm_start_files_data['processing_latency_ms'].mean()
        localstack_std = localstack_warm_start_files['processing_latency_ms'].std()
        aws_std = aws_warm_start_files_data['processing_latency_ms'].std()
        
        labels = ['LocalStack\n(Warm Start)', 'AWS\n(Warm Start)']
        means = [localstack_mean, aws_mean]
        stds = [localstack_std, aws_std]
        colors = ['#3498db', '#2ecc71']
        counts = [len(localstack_warm_start_files), len(aws_warm_start_files_data)]
        
        bars = ax2.bar(
            labels,
            means,
            color=colors,
            alpha=0.8,
            edgecolor='black',
            linewidth=1.5,
            yerr=stds,
            capsize=10,
            error_kw={'elinewidth': 2, 'capthick': 2}
        )
        
        # Add value labels
        for bar, mean_val, std_val, count in zip(bars, means, stds, counts):
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + std_val + 30,
                f'{mean_val:.1f} ms\n(±{std_val:.1f} ms)\nn={count}',
                ha='center',
                va='bottom',
                fontsize=10,
                fontweight='bold'
            )
        
        # Calculate and display environment difference
        diff = aws_mean - localstack_mean
        diff_pct = (diff / localstack_mean) * 100 if localstack_mean > 0 else 0
        
        diff_text = f'Environment Difference: {diff:+.1f}ms ({diff_pct:+.1f}%)'
        ax2.text(
            0.5, 0.95,
            diff_text,
            transform=ax2.transAxes,
            ha='center',
            fontsize=11,
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8),
            verticalalignment='top'
        )
        
        ax2.set_ylabel('Average Processing Latency (ms)', fontsize=12)
        ax2.set_title(f'Warm Start Files: LocalStack vs AWS (Both Warm)\n{len(aws_warm_start_files)} files', 
                      fontsize=13, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.set_ylim(0, max(means) + max(stds) + 100)
    
    plt.tight_layout()
    output_path2 = os.path.join(output_dir, 'plot_c2_warm_start_files.png')
    plt.savefig(output_path2, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"✓ Saved: {output_path2}")


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
    plot_cold_start_penalty_overall(df, args.output_dir)  # Overall comparison
    plot_cold_start_penalty(df, args.output_dir)  # Detailed breakdown (C1 and C2)
    
    print(f"\n✓ All plots generated successfully!")


if __name__ == "__main__":
    main()

