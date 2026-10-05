"""Statistical metrics and paired comparisons for the evaluation."""

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.metrics import accuracy_score, cohen_kappa_score, f1_score


CASE_FINDING_POSITIVE_LABELS = frozenset({'eligible', 'potentially eligible'})
DEFAULT_BOOTSTRAP_RESAMPLES = 1000
RANDOM_SEED = 42


def _clean_label_pairs(y_true, y_pred, labels):
    """Return aligned arrays containing only valid reference/prediction labels."""
    true_series = pd.Series(y_true).reset_index(drop=True)
    pred_series = pd.Series(y_pred).reset_index(drop=True)
    valid = true_series.isin(labels) & pred_series.isin(labels)
    return true_series[valid].to_numpy(), pred_series[valid].to_numpy()


def _safe_ratio(numerator, denominator):
    """Divide counts, returning NaN when the denominator is zero."""
    if denominator == 0:
        return np.nan
    return numerator / denominator


def _binary_counts(y_true, y_pred, positive_labels=CASE_FINDING_POSITIVE_LABELS):
    """Count case-finding true and false positives and negatives."""
    true_positive_class = np.isin(y_true, list(positive_labels))
    pred_positive_class = np.isin(y_pred, list(positive_labels))
    tp = int(np.sum(true_positive_class & pred_positive_class))
    fn = int(np.sum(true_positive_class & ~pred_positive_class))
    fp = int(np.sum(~true_positive_class & pred_positive_class))
    tn = int(np.sum(~true_positive_class & ~pred_positive_class))
    return tp, fn, fp, tn


def _candidate_sensitivity(y_true, y_pred, positive_labels=CASE_FINDING_POSITIVE_LABELS):
    """Calculate case-finding sensitivity from binary counts."""
    tp, fn, _, _ = _binary_counts(y_true, y_pred, positive_labels)
    return _safe_ratio(tp, tp + fn)


def _candidate_precision(y_true, y_pred, positive_labels=CASE_FINDING_POSITIVE_LABELS):
    """Calculate case-finding positive predictive value."""
    tp, _, fp, _ = _binary_counts(y_true, y_pred, positive_labels)
    return _safe_ratio(tp, tp + fp)


def _candidate_specificity(y_true, y_pred, positive_labels=CASE_FINDING_POSITIVE_LABELS):
    """Calculate case-finding specificity from binary counts."""
    _, _, fp, tn = _binary_counts(y_true, y_pred, positive_labels)
    return _safe_ratio(tn, tn + fp)


def _candidate_npv(y_true, y_pred, positive_labels=CASE_FINDING_POSITIVE_LABELS):
    """Calculate case-finding negative predictive value."""
    _, fn, _, tn = _binary_counts(y_true, y_pred, positive_labels)
    return _safe_ratio(tn, tn + fn)


def _class_recall(y_true, y_pred, label):
    """Calculate recall for one eligibility class."""
    true_label = y_true == label
    return _safe_ratio(np.sum(true_label & (y_pred == label)), np.sum(true_label))


def _class_precision(y_true, y_pred, label):
    """Calculate precision for one eligibility class."""
    pred_label = y_pred == label
    return _safe_ratio(np.sum((y_true == label) & pred_label), np.sum(pred_label))


def _class_f1(y_true, y_pred, label):
    """Calculate the F1 score for one eligibility class."""
    recall = _class_recall(y_true, y_pred, label)
    precision = _class_precision(y_true, y_pred, label)
    if not np.isfinite(recall) or not np.isfinite(precision):
        return np.nan
    if precision + recall == 0:
        return 0.0
    return _safe_ratio(2 * precision * recall, precision + recall)


def _bootstrap_ci(y_true, y_pred, metric_func,
                  n_resamples=DEFAULT_BOOTSTRAP_RESAMPLES, seed=RANDOM_SEED):
    """Return point estimate and paired case-resampling percentile CI."""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    point = float(metric_func(y_true, y_pred))
    if len(y_true) == 0:
        return point, np.nan, np.nan

    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(n_resamples):
        indices = rng.choice(len(y_true), len(y_true), replace=True)
        estimate = metric_func(y_true[indices], y_pred[indices])
        if np.isfinite(estimate):
            estimates.append(float(estimate))

    if not estimates:
        return point, np.nan, np.nan
    lower, upper = np.percentile(estimates, [2.5, 97.5])
    return point, float(lower), float(upper)


def _paired_bootstrap_difference(y_true, pred_a, pred_b, metric_func,
                                 n_resamples=DEFAULT_BOOTSTRAP_RESAMPLES,
                                 seed=RANDOM_SEED):
    """Return A-B metric difference and a paired percentile bootstrap CI."""
    y_true = np.asarray(y_true)
    pred_a = np.asarray(pred_a)
    pred_b = np.asarray(pred_b)
    point = float(metric_func(y_true, pred_a) - metric_func(y_true, pred_b))
    if len(y_true) == 0:
        return point, np.nan, np.nan

    rng = np.random.default_rng(seed)
    differences = []
    for _ in range(n_resamples):
        indices = rng.choice(len(y_true), len(y_true), replace=True)
        difference = (
            metric_func(y_true[indices], pred_a[indices])
            - metric_func(y_true[indices], pred_b[indices])
        )
        if np.isfinite(difference):
            differences.append(float(difference))

    if not differences:
        return point, np.nan, np.nan
    lower, upper = np.percentile(differences, [2.5, 97.5])
    return point, float(lower), float(upper)


def calculate_metrics(y_true, y_pred, system_name, reference_name, labels,
                      positive_labels=CASE_FINDING_POSITIVE_LABELS,
                      n_resamples=DEFAULT_BOOTSTRAP_RESAMPLES):
    """Calculate multiclass and clinically motivated binary case-finding metrics."""
    y_true, y_pred = _clean_label_pairs(y_true, y_pred, labels)
    metric_functions = {
        'Accuracy': accuracy_score,
        'Weighted F1': lambda yt, yp: f1_score(
            yt, yp, average='weighted', labels=labels, zero_division=0
        ),
        "Cohen's kappa": lambda yt, yp: cohen_kappa_score(yt, yp, labels=labels),
        'Case-finding sensitivity': lambda yt, yp: _candidate_sensitivity(
            yt, yp, positive_labels
        ),
        'Case-finding precision (PPV)': lambda yt, yp: _candidate_precision(
            yt, yp, positive_labels
        ),
        'Case-finding specificity': lambda yt, yp: _candidate_specificity(
            yt, yp, positive_labels
        ),
        'Case-finding NPV': lambda yt, yp: _candidate_npv(yt, yp, positive_labels),
    }

    row = {
        'Comparison': f'{system_name} vs {reference_name}',
        'System': system_name,
        'Reference': reference_name,
        'N': int(len(y_true)),
        'Correct': int(np.sum(y_true == y_pred)),
        'Errors': int(np.sum(y_true != y_pred)),
    }
    for metric_name, metric_func in metric_functions.items():
        point, lower, upper = _bootstrap_ci(
            y_true, y_pred, metric_func, n_resamples=n_resamples
        )
        row[metric_name] = point
        row[f'{metric_name} CI lower'] = lower
        row[f'{metric_name} CI upper'] = upper

    return row


def calculate_class_specific_metrics(y_true, y_pred, system_name, reference_name, labels,
                                     n_resamples=DEFAULT_BOOTSTRAP_RESAMPLES):
    """Calculate one-vs-rest precision, recall/sensitivity, and F1 for every class."""
    y_true, y_pred = _clean_label_pairs(y_true, y_pred, labels)
    rows = []
    for label in labels:
        metric_functions = {
            'Recall (sensitivity)': lambda yt, yp, current=label: _class_recall(
                yt, yp, current
            ),
            'Precision (PPV)': lambda yt, yp, current=label: _class_precision(
                yt, yp, current
            ),
            'F1': lambda yt, yp, current=label: _class_f1(yt, yp, current),
        }
        row = {
            'System': system_name,
            'Reference': reference_name,
            'Class': label,
            'N': int(len(y_true)),
            'Support': int(np.sum(y_true == label)),
            'Predicted': int(np.sum(y_pred == label)),
        }
        for metric_name, metric_func in metric_functions.items():
            point, lower, upper = _bootstrap_ci(
                y_true, y_pred, metric_func, n_resamples=n_resamples
            )
            row[metric_name] = point
            row[f'{metric_name} CI lower'] = lower
            row[f'{metric_name} CI upper'] = upper
        rows.append(row)
    return rows


def paired_classifier_comparison(y_true, pred_a, pred_b, name_a, name_b, labels,
                                 positive_labels=CASE_FINDING_POSITIVE_LABELS,
                                 n_resamples=DEFAULT_BOOTSTRAP_RESAMPLES):
    """Compare two classifiers evaluated on the same cases.

    The exact McNemar test compares paired overall correctness. Metric
    differences use paired case-resampling so both systems always see the same
    bootstrap sample.
    """
    true_series = pd.Series(y_true).reset_index(drop=True)
    a_series = pd.Series(pred_a).reset_index(drop=True)
    b_series = pd.Series(pred_b).reset_index(drop=True)
    valid = (
        true_series.isin(labels)
        & a_series.isin(labels)
        & b_series.isin(labels)
    )
    y_true = true_series[valid].to_numpy()
    pred_a = a_series[valid].to_numpy()
    pred_b = b_series[valid].to_numpy()

    a_correct = pred_a == y_true
    b_correct = pred_b == y_true
    a_only = int(np.sum(a_correct & ~b_correct))
    b_only = int(np.sum(~a_correct & b_correct))
    discordant = a_only + b_only
    mcnemar_p = (
        float(binomtest(a_only, discordant, p=0.5, alternative='two-sided').pvalue)
        if discordant else 1.0
    )

    metric_functions = {
        'Accuracy difference': accuracy_score,
        'Weighted F1 difference': lambda yt, yp: f1_score(
            yt, yp, average='weighted', labels=labels, zero_division=0
        ),
        "Cohen's kappa difference": lambda yt, yp: cohen_kappa_score(
            yt, yp, labels=labels
        ),
        'Case-finding sensitivity difference': lambda yt, yp: _candidate_sensitivity(
            yt, yp, positive_labels
        ),
        'Case-finding precision difference': lambda yt, yp: _candidate_precision(
            yt, yp, positive_labels
        ),
    }
    row = {
        'Comparison': f'{name_a} minus {name_b}',
        'System A': name_a,
        'System B': name_b,
        'N': int(len(y_true)),
        'Both correct': int(np.sum(a_correct & b_correct)),
        'System A only correct': a_only,
        'System B only correct': b_only,
        'Both incorrect': int(np.sum(~a_correct & ~b_correct)),
        'Discordant correctness pairs': discordant,
        'Exact McNemar p-value': mcnemar_p,
    }
    for metric_name, metric_func in metric_functions.items():
        point, lower, upper = _paired_bootstrap_difference(
            y_true, pred_a, pred_b, metric_func, n_resamples=n_resamples
        )
        row[metric_name] = point
        row[f'{metric_name} CI lower'] = lower
        row[f'{metric_name} CI upper'] = upper
    return row
