"""Held-out classifier metrics and VALIDATION-only selective decision policy."""
from __future__ import annotations
import math


def classification_report(y_true, scores, labels):
    import numpy as np
    y_true = np.asarray(y_true, dtype=int)
    scores = np.asarray(scores, dtype=float)
    if scores.shape != (len(y_true), len(labels)) or len(y_true) == 0:
        raise ValueError('Score shape must match non-empty targets and exact ordered labels.')
    if not np.isfinite(scores).all() or (scores < 0).any() or (scores > 1).any() or not np.allclose(scores.sum(axis=1), 1, atol=1e-3):
        raise ValueError('Expected one finite probability vector per image; do not apply softmax twice.')
    predicted = scores.argmax(axis=1)
    confidence = scores.max(axis=1)
    confusion = np.zeros((len(labels), len(labels)), dtype=int)
    np.add.at(confusion, (y_true, predicted), 1)
    per_class = {}
    for index, label in enumerate(labels):
        true_positive = int(confusion[index, index])
        support = int(confusion[index].sum())
        predicted_count = int(confusion[:, index].sum())
        precision = true_positive / predicted_count if predicted_count else 0.0
        recall = true_positive / support if support else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {'precision': precision, 'recall': recall, 'f1': f1, 'support': support}
    correct = predicted == y_true
    reliability, ece = [], 0.0
    for index in range(10):
        lower, upper = index / 10, (index + 1) / 10
        selected = (confidence >= lower) & ((confidence < upper) if index < 9 else (confidence <= upper))
        count = int(selected.sum())
        accuracy = float(correct[selected].mean()) if count else None
        mean_score = float(confidence[selected].mean()) if count else None
        if count:
            ece += count / len(y_true) * abs(accuracy - mean_score)
        reliability.append({'lower': lower, 'upper': upper, 'count': count, 'accuracy': accuracy, 'mean_score': mean_score})
    one_hot = np.eye(len(labels))[y_true]
    return {'n': len(y_true), 'accuracy': float(correct.mean()),
            'macro_f1': sum(row['f1'] for row in per_class.values()) / len(labels),
            'per_class': per_class, 'confusion_matrix': confusion.tolist(), 'ordered_labels': labels,
            'reliability': {'calibration': 'uncalibrated', 'bins': reliability, 'expected_calibration_error': float(ece),
                            'multiclass_brier_score': float(np.square(scores - one_hot).sum(axis=1).mean()),
                            'negative_log_likelihood': float(-np.log(np.maximum(scores[np.arange(len(y_true)), y_true], 1e-12)).mean())}}


def wilson_lower(correct: int, count: int, z: float = 1.96) -> float:
    if count == 0:
        return 0.0
    proportion = correct / count
    denominator = 1 + z * z / count
    center = proportion + z * z / (2 * count)
    radius = z * math.sqrt(proportion * (1 - proportion) / count + z * z / (4 * count * count))
    return (center - radius) / denominator


def choose_policy(y_true, scores, target_precision=.98, min_accepted=100):
    import numpy as np
    scores = np.asarray(scores, dtype=float)
    correct = scores.argmax(axis=1) == np.asarray(y_true)
    ordered = np.sort(scores, axis=1)
    top, margin = ordered[:, -1], ordered[:, -1] - ordered[:, -2]
    best = None
    score_grid = np.unique(np.r_[.5, np.quantile(top, np.linspace(0, 1, 31)), .999])
    margin_grid = np.unique(np.r_[0., np.quantile(margin, np.linspace(0, 1, 21))])
    for threshold in score_grid:
        for gap in margin_grid:
            selected = (top >= threshold) & (margin >= gap)
            count = int(selected.sum())
            successes = int(correct[selected].sum())
            if count < min_accepted or successes / count < target_precision or wilson_lower(successes, count) < .95:
                continue
            candidate = {'min_score': float(threshold), 'min_margin': float(gap), 'validated': True,
                         'selection_split': 'validation', 'target_precision': target_precision,
                         'validation_accepted': count, 'validation_total': len(scores),
                         'validation_selective_accuracy': successes / count,
                         'validation_coverage': count / len(scores), 'wilson_lower_95': wilson_lower(successes, count),
                         'calibration_status': 'uncalibrated',
                         'limitations': 'Validation-tuned closed-set selection only. Not proof of non-leaf/unknown-species rejection. Selection statistics are optimistic because thresholds use this validation split.'}
            if best is None or count > best['validation_accepted']:
                best = candidate
    return best or {'min_score': 1.0, 'min_margin': 1.0, 'validated': False,
                    'selection_split': 'validation', 'target_precision': target_precision,
                    'validation_total': len(scores), 'min_accepted_required': min_accepted,
                    'reason': 'No validation policy met selective-accuracy/support requirements; all results remain uncertain.'}


def selective_report(y_true, scores, policy):
    import numpy as np
    scores = np.asarray(scores)
    ordered = np.sort(scores, axis=1)
    selected = ((ordered[:, -1] >= policy['min_score']) &
                (ordered[:, -1] - ordered[:, -2] >= policy['min_margin'])) if policy.get('validated') else np.zeros(len(scores), dtype=bool)
    count = int(selected.sum())
    correct = scores.argmax(axis=1) == np.asarray(y_true)
    return {'accepted_count': count, 'coverage': count / len(scores),
            'selective_accuracy': float(correct[selected].mean()) if count else None,
            'warning': 'Coverage/accuracy apply to this measured split only, not arbitrary user photos.'}
