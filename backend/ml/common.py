"""Pure helpers shared by dataset preparation and training; no TensorFlow import."""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: str | Path, value: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def available_memory_bytes() -> int | None:
    """Available memory, not total installed memory; supports Windows and Linux."""
    if sys.platform == 'win32':
        import ctypes
        class MemoryStatus(ctypes.Structure):
            _fields_ = [('length', ctypes.c_ulong), ('load', ctypes.c_ulong),
                        ('total_physical', ctypes.c_ulonglong), ('available_physical', ctypes.c_ulonglong),
                        ('total_pagefile', ctypes.c_ulonglong), ('available_pagefile', ctypes.c_ulonglong),
                        ('total_virtual', ctypes.c_ulonglong), ('available_virtual', ctypes.c_ulonglong),
                        ('available_extended', ctypes.c_ulonglong)]
        status = MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return int(status.available_physical)
    elif Path('/proc/meminfo').exists():
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) * 1024
    return None


def preflight_memory(minimum_gib: float, allow_low_memory: bool = False) -> int | None:
    available = available_memory_bytes()
    if available is not None and available < minimum_gib * 1024**3 and not allow_low_memory:
        raise RuntimeError(
            f'Only {available / 1024**3:.2f} GiB RAM currently available; '
            f'this command requires at least {minimum_gib:.1f} GiB before importing TensorFlow. '
            'Close memory-heavy applications or run the Colab notebook. '
            '--allow-low-memory bypasses this guard at your own resource risk; it does not reduce memory usage.')
    return available


class UnionFind:
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, item: int) -> int:
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left: int, right: int) -> None:
        left, right = self.find(left), self.find(right)
        if left == right:
            return
        if self.rank[left] < self.rank[right]:
            left, right = right, left
        self.parent[right] = left
        if self.rank[left] == self.rank[right]:
            self.rank[left] += 1


class HashTree:
    """BK-tree for conservative Hamming-distance duplicate candidates."""
    def __init__(self):
        self.root = None

    def add(self, value: int, index: int) -> None:
        node = [value, index, {}]
        if self.root is None:
            self.root = node
            return
        current = self.root
        while True:
            distance = (current[0] ^ value).bit_count()
            if distance not in current[2]:
                current[2][distance] = node
                return
            current = current[2][distance]

    def query(self, value: int, radius: int) -> list[int]:
        result = []
        stack = [self.root] if self.root is not None else []
        while stack:
            current = stack.pop()
            distance = (current[0] ^ value).bit_count()
            if distance <= radius:
                result.append(current[1])
            stack.extend(node for edge, node in current[2].items() if distance - radius <= edge <= distance + radius)
        return result


def group_records(records: list[dict], near_distance: int = 2) -> tuple[list[dict], list[dict]]:
    """Group canonical pixels, source IDs and conservative perceptual matches globally.

    Cross-label components are excluded instead of choosing one label. Transitive
    grouping can over-group similar leaves; it reduces leakage but does not prove
    independence between photos. Never present it as a perfect source grouping.
    """
    union = UnionFind(len(records))
    exact, source = {}, {}
    tree = HashTree()
    for index, record in enumerate(records):
        for mapping, key in [(exact, record['pixel_sha256']), (source, record.get('source_group'))]:
            if key:
                if key in mapping:
                    union.union(index, mapping[key])
                else:
                    mapping[key] = index
        if near_distance >= 0:
            perceptual = int(record['dhash'], 16)
            for candidate in tree.query(perceptual, near_distance):
                union.union(index, candidate)
            tree.add(perceptual, index)
    grouped = defaultdict(list)
    for index, record in enumerate(records):
        grouped[union.find(index)].append(record)
    accepted, conflicts = [], []
    for items in grouped.values():
        group_id = min(item['pixel_sha256'] for item in items)
        if len({item['label_index'] for item in items}) > 1:
            conflicts.append({'group_id': group_id, 'records': items, 'reason': 'duplicate_group_label_conflict'})
        else:
            accepted.extend(dict(item, group_id=group_id) for item in items)
    return accepted, conflicts


def stratified_group_split(records: list[dict], labels: list[str], seed: int = 42,
                           fractions: tuple[float, float, float] = (.7, .15, .15)) -> tuple[dict, dict]:
    if len(fractions) != 3 or any(x <= 0 for x in fractions) or not math.isclose(sum(fractions), 1):
        raise ValueError('Three positive split fractions must sum to one.')
    names = ('train', 'validation', 'test')
    by_label = defaultdict(lambda: defaultdict(list))
    for item in records:
        index = item['label_index']
        if not 0 <= index < len(labels):
            raise ValueError('Label index lies outside the authoritative ordered label list.')
        by_label[index][item['group_id']].append(item)
    result = {name: [] for name in names}
    statistics = {}
    for index, label in enumerate(labels):
        groups = list(by_label[index].values())
        if len(groups) < 3:
            raise ValueError(f'{label}: only {len(groups)} independent groups; cannot populate three splits safely.')
        # Seeded ties, then largest-first weighted packing. Every class gets each
        # split, while large duplicate components remain intact.
        rng = random.Random(f'{seed}:{index}')
        groups.sort(key=lambda values: values[0]['group_id'])
        rng.shuffle(groups)
        groups.sort(key=len, reverse=True)
        total = sum(map(len, groups))
        targets = [total * fraction for fraction in fractions]
        counts = [0, 0, 0]
        assigned = [[], [], []]
        for group_index, group in enumerate(groups):
            empty = [position for position, count in enumerate(counts) if count == 0]
            remaining = len(groups) - group_index
            choices = empty if len(empty) == remaining else range(3)
            destination = max(choices, key=lambda position: (targets[position] - counts[position]) / targets[position])
            assigned[destination].extend(group)
            counts[destination] += len(group)
        statistics[label] = dict(zip(names, counts), groups=len(groups), total=total,
                                 requested_fractions=list(fractions), achieved_fractions=[value / total for value in counts])
        for name, items in zip(names, assigned):
            result[name].extend(items)
    for name in names:
        result[name].sort(key=lambda item: (item['label_index'], item['pixel_sha256'], item['filename']))
    return result, statistics


def validate_manifests(directory: Path) -> tuple[list[str], dict]:
    labels = load_json(directory / 'class_labels.json')
    if not isinstance(labels, list) or not labels or len(labels) != len(set(labels)) or not all(isinstance(x, str) for x in labels):
        raise ValueError('class_labels.json must be the unique ordered string label list.')
    seen_groups = {}
    manifests = {}
    for split in ('train', 'validation', 'test'):
        rows = [json.loads(line) for line in (directory / f'{split}.jsonl').read_text(encoding='utf-8').splitlines() if line]
        if not rows:
            raise ValueError(f'{split} manifest is empty.')
        for row in rows:
            if not 0 <= row['label_index'] < len(labels) or row['label'] != labels[row['label_index']]:
                raise ValueError('Manifest label-index ordering is inconsistent.')
            group = row['group_id']
            if group in seen_groups and seen_groups[group] != split:
                raise ValueError(f'Duplicate group spans {seen_groups[group]} and {split}.')
            seen_groups[group] = split
            path = (directory / row['path']).resolve()
            if not path.is_relative_to(directory.resolve()) or not path.is_file():
                raise ValueError(f'Manifest image missing or outside prepared directory: {row["path"]}')
        manifests[split] = rows
    return labels, manifests
