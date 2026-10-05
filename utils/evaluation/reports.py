"""Tables and figures for evaluation results."""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import cohen_kappa_score, confusion_matrix

from .statistics import DEFAULT_BOOTSTRAP_RESAMPLES, RANDOM_SEED, _clean_label_pairs, _safe_ratio


def _format_estimate_ci(row, metric_name, digits=3):
    """Format a metric and its confidence interval for publication."""
    point = row.get(metric_name, np.nan)
    lower = row.get(f'{metric_name} CI lower', np.nan)
    upper = row.get(f'{metric_name} CI upper', np.nan)
    if not np.isfinite(point):
        return 'N/A'
    if not np.isfinite(lower) or not np.isfinite(upper):
        return f'{point:.{digits}f}'
    return f'{point:.{digits}f} ({lower:.{digits}f}-{upper:.{digits}f})'


def _write_dataframe(df, xlsx_path, md_path, markdown_df=None):
    """Write a table as Excel and Markdown files."""
    df.to_excel(xlsx_path, index=False)
    table = markdown_df if markdown_df is not None else df
    with open(md_path, 'w', encoding='utf-8') as handle:
        handle.write(table.to_markdown(index=False))
        handle.write('\n')


def write_summary_files(metrics_rows, class_metric_rows, y_true, prediction_agents,
                        reference_name, labels, output_dir):
    """Write raw Excel workbooks and compact Markdown tables for manuscript use."""
    metrics_df = pd.DataFrame(metrics_rows)
    metric_names = [
        'Accuracy', 'Weighted F1', "Cohen's kappa",
        'Case-finding sensitivity', 'Case-finding precision (PPV)',
        'Case-finding specificity', 'Case-finding NPV',
    ]
    publication_rows = []
    for row in metrics_rows:
        publication_row = {
            'System': row['System'],
            'N': row['N'],
            'Correct': row['Correct'],
            'Errors': row['Errors'],
        }
        for metric_name in metric_names:
            publication_label = (
                'Case-finding precision/PPV'
                if metric_name == 'Case-finding precision (PPV)'
                else metric_name
            )
            publication_row[f'{publication_label} (95% CI)'] = (
                _format_estimate_ci(row, metric_name)
            )
        publication_rows.append(publication_row)
    publication_df = pd.DataFrame(publication_rows)
    _write_dataframe(
        metrics_df,
        os.path.join(output_dir, 'results_summary.xlsx'),
        os.path.join(output_dir, 'results_summary.md'),
        publication_df,
    )
    with open(os.path.join(output_dir, 'results_summary.md'), 'a', encoding='utf-8') as handle:
        handle.write(
            '\nCase-finding positive class: `eligible` or `potentially eligible`; '
            f'95% CIs use {DEFAULT_BOOTSTRAP_RESAMPLES} case-level bootstrap resamples '
            f'(seed {RANDOM_SEED}).\n'
        )

    class_df = pd.DataFrame(class_metric_rows)
    class_publication_rows = []
    for row in class_metric_rows:
        class_publication_rows.append({
            'System': row['System'],
            'Class': row['Class'],
            'Support': row['Support'],
            'Predicted': row['Predicted'],
            'Recall/sensitivity (95% CI)': _format_estimate_ci(
                row, 'Recall (sensitivity)'
            ),
            'Precision/PPV (95% CI)': _format_estimate_ci(row, 'Precision (PPV)'),
            'F1 (95% CI)': _format_estimate_ci(row, 'F1'),
        })
    _write_dataframe(
        class_df,
        os.path.join(output_dir, 'class_specific_metrics.xlsx'),
        os.path.join(output_dir, 'class_specific_metrics.md'),
        pd.DataFrame(class_publication_rows),
    )

    true_series = pd.Series(y_true)
    distribution_rows = []
    systems = [(reference_name, true_series)] + [
        (agent['name'], pd.Series(agent['series'])) for agent in prediction_agents
    ]
    for system_name, series in systems:
        valid = series[series.isin(labels)]
        total = len(valid)
        for label in labels:
            count = int(np.sum(valid == label))
            distribution_rows.append({
                'System': system_name,
                'Class': label,
                'Count': count,
                'Percent': _safe_ratio(100 * count, total),
                'N': total,
            })
    distribution_df = pd.DataFrame(distribution_rows)
    distribution_publication = distribution_df.copy()
    distribution_publication['Count (%)'] = distribution_publication.apply(
        lambda row: f"{int(row['Count'])} ({row['Percent']:.1f}%)", axis=1
    )
    distribution_publication = distribution_publication[
        ['System', 'Class', 'Count (%)', 'N']
    ]
    _write_dataframe(
        distribution_df,
        os.path.join(output_dir, 'label_distribution.xlsx'),
        os.path.join(output_dir, 'label_distribution.md'),
        distribution_publication,
    )


def write_paired_comparison_files(rows, output_dir):
    """Write paired model-versus-rule comparison tables."""
    if not rows:
        return
    comparison_df = pd.DataFrame(rows)
    publication_rows = []
    difference_names = [
        'Accuracy difference', 'Weighted F1 difference',
        "Cohen's kappa difference", 'Case-finding sensitivity difference',
        'Case-finding precision difference',
    ]
    for row in rows:
        publication_row = {
            'Comparison': row['Comparison'],
            'N': row['N'],
            'Both correct': row['Both correct'],
            'System A only correct': row['System A only correct'],
            'System B only correct': row['System B only correct'],
            'Both incorrect': row['Both incorrect'],
            'Exact McNemar p-value': f"{row['Exact McNemar p-value']:.4f}",
        }
        for difference_name in difference_names:
            publication_row[f'{difference_name} (95% CI)'] = _format_estimate_ci(
                row, difference_name
            )
        publication_rows.append(publication_row)
    _write_dataframe(
        comparison_df,
        os.path.join(output_dir, 'paired_llm_vs_rule_based_comparison.xlsx'),
        os.path.join(output_dir, 'paired_llm_vs_rule_based_comparison.md'),
        pd.DataFrame(publication_rows),
    )
    with open(
        os.path.join(output_dir, 'paired_llm_vs_rule_based_comparison.md'),
        'a', encoding='utf-8',
    ) as handle:
        handle.write(
            '\nThe exact two-sided McNemar test compares paired overall correctness. '
            f'Difference CIs use {DEFAULT_BOOTSTRAP_RESAMPLES} paired case-level '
            f'bootstrap resamples (seed {RANDOM_SEED}).\n'
        )


def _confusion_plot_name(name):
    """Wrap the rule-based comparator name for confusion plots."""
    if name == 'Deterministic rule-based comparator':
        return 'Deterministic rule-based\ncomparator'
    return name


def _confusion_for_agent(y_true, y_pred, labels):
    """Build a confusion matrix from valid paired labels."""
    clean_true, clean_pred = _clean_label_pairs(y_true, y_pred, labels)
    return confusion_matrix(clean_true, clean_pred, labels=labels)


def create_confusion_matrix_figures(y_true, prediction_agents, reference_name, labels,
                                    output_dir, dataset_slug):
    """Write individual matrices and a publication-ready multi-panel figure."""
    if not prediction_agents:
        return
    plot_labels = [label.capitalize().replace(' ', '\n') for label in labels]
    matrices = [
        _confusion_for_agent(y_true, agent['series'], labels)
        for agent in prediction_agents
    ]
    vmax = max(int(matrix.max()) for matrix in matrices) if matrices else 1

    for agent, matrix in zip(prediction_agents, matrices):
        plt.figure(figsize=(5, 4))
        sns.heatmap(
            matrix, annot=True, fmt='d', cmap='Blues', vmin=0, vmax=vmax,
            xticklabels=plot_labels, yticklabels=plot_labels,
        )
        plt.title(f"{_confusion_plot_name(agent['name'])} vs {reference_name}")
        plt.ylabel('Reference label', labelpad=10)
        plt.xlabel('Predicted label', labelpad=10)
        plt.yticks(rotation=0)
        plt.tight_layout()
        file_stem = agent['file_stem']
        plt.savefig(
            os.path.join(output_dir, f'confusion_matrix_{file_stem}.png'),
            dpi=300, bbox_inches='tight',
        )
        plt.close()

    panel_count = len(prediction_agents)
    fig, axes = plt.subplots(
        1, panel_count, figsize=(4.1 * panel_count, 4.1), squeeze=False,
        sharex=True, sharey=True,
    )
    for axis, agent, matrix in zip(axes[0], prediction_agents, matrices):
        sns.heatmap(
            matrix, annot=True, fmt='d', cmap='Blues', vmin=0, vmax=vmax,
            xticklabels=plot_labels, yticklabels=plot_labels, cbar=False, ax=axis,
        )
        axis.set_title(
            f"{_confusion_plot_name(agent['name'])} vs {reference_name}",
            fontsize=11,
        )
        axis.set_xlabel('')
        axis.set_ylabel('')
        axis.tick_params(axis='x', rotation=0)
        axis.tick_params(axis='y', rotation=0)
    fig.supxlabel('Predicted label')
    fig.supylabel('Reference label')
    fig.tight_layout(rect=(0.02, 0.04, 1, 1))
    fig.savefig(
        os.path.join(output_dir, f'figure_{dataset_slug}_confusion_matrices.png'),
        dpi=300, bbox_inches='tight',
    )
    plt.close(fig)


def _agreement_matrix(y_true, prediction_agents, reference_name, labels):
    """Calculate pairwise Cohen kappa values across agents."""
    names = [agent['name'] for agent in prediction_agents] + [reference_name]
    series = [pd.Series(agent['series']) for agent in prediction_agents] + [
        pd.Series(y_true)
    ]
    matrix = pd.DataFrame(index=names, columns=names, dtype=float)
    for i, (name_i, series_i) in enumerate(zip(names, series)):
        for j, (name_j, series_j) in enumerate(zip(names, series)):
            if i == j:
                matrix.loc[name_i, name_j] = 1.0
                continue
            clean_i, clean_j = _clean_label_pairs(series_i, series_j, labels)
            matrix.loc[name_i, name_j] = cohen_kappa_score(
                clean_i, clean_j, labels=labels
            )
    return matrix


def _short_plot_name(name):
    """Shorten the rule-based comparator name for bar plots."""
    if name == 'Deterministic rule-based comparator':
        return 'Rule-based\ncomparator'
    return name


def _heatmap_plot_name(name):
    """Shorten the rule-based comparator name for heatmaps."""
    if name == 'Deterministic rule-based comparator':
        return 'Rule-based\ncomparator'
    return name


def create_performance_and_agreement_figures(metrics_rows, y_true, prediction_agents,
                                             reference_name, labels, output_dir,
                                             dataset_slug):
    """Write the Kappa bar plot, agreement heatmap, and their combined figure."""
    if not prediction_agents:
        return
    metrics_by_system = {row['System']: row for row in metrics_rows}
    plot_agents = [
        agent for agent in prediction_agents if agent['name'] in metrics_by_system
    ]
    names = [agent['name'] for agent in plot_agents]
    kappas = [metrics_by_system[name]["Cohen's kappa"] for name in names]
    short_names = [_short_plot_name(name) for name in names]
    agreement = _agreement_matrix(y_true, plot_agents, reference_name, labels)

    bar_width = max(5, 1.25 * len(names))
    fig, axis = plt.subplots(figsize=(bar_width, 4.5))
    colors = sns.color_palette('magma', n_colors=len(names))
    bars = axis.bar(short_names, kappas, color=colors)
    axis.set_title(f"Performance vs {reference_name}")
    axis.set_ylabel("Cohen's kappa")
    axis.set_ylim(min(0, min(kappas) - 0.1), 1.05)
    axis.bar_label(bars, labels=[f'{value:.2f}' for value in kappas], padding=3)
    fig.tight_layout()
    fig.savefig(
        os.path.join(output_dir, 'performance_benchmark.png'),
        dpi=300, bbox_inches='tight',
    )
    plt.close(fig)

    heatmap_size = max(5, len(agreement) * 1.05)
    fig, axis = plt.subplots(figsize=(heatmap_size, heatmap_size * 0.85))
    agreement_for_plot = agreement.rename(
        index=_heatmap_plot_name, columns=_heatmap_plot_name
    )
    sns.heatmap(
        agreement_for_plot, annot=True, fmt='.2f', cmap='vlag',
        vmin=-1, vmax=1, center=0,
        square=True, ax=axis,
    )
    axis.set_title("Inter-agent agreement (Cohen's kappa)")
    axis.tick_params(axis='x', rotation=45)
    axis.tick_params(axis='y', rotation=0)
    fig.tight_layout()
    fig.savefig(
        os.path.join(output_dir, 'agreement_heatmap.png'),
        dpi=300, bbox_inches='tight',
    )
    plt.close(fig)

    combined_width = max(11, 1.4 * len(names) + 6)
    fig, (bar_axis, heatmap_axis) = plt.subplots(
        1, 2, figsize=(combined_width, 5.2),
        gridspec_kw={'width_ratios': [max(1.0, len(names) / 2.5), 1.4]},
    )
    bars = bar_axis.bar(short_names, kappas, color=colors)
    bar_axis.set_title(f"Performance vs {reference_name}")
    bar_axis.set_ylabel("Cohen's kappa")
    bar_axis.set_ylim(min(0, min(kappas) - 0.1), 1.05)
    bar_axis.bar_label(bars, labels=[f'{value:.2f}' for value in kappas], padding=3)
    sns.heatmap(
        agreement_for_plot, annot=True, fmt='.2f', cmap='vlag',
        vmin=-1, vmax=1, center=0,
        square=True, ax=heatmap_axis,
    )
    heatmap_axis.set_title("Inter-agent agreement (Cohen's kappa)")
    heatmap_axis.tick_params(axis='x', rotation=45)
    heatmap_axis.tick_params(axis='y', rotation=0)
    fig.tight_layout()
    fig.savefig(
        os.path.join(
            output_dir, f'figure_{dataset_slug}_performance_and_agreement.png'
        ),
        dpi=300, bbox_inches='tight',
    )
    plt.close(fig)
