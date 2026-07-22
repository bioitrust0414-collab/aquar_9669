#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path

import yaml

REPO = Path('/home/ubuntu/work/aquar_9669_current')
SOURCE = REPO / 'docs' / 'publish-schedule-v2.json'
OUTPUT = REPO / '.audit' / 'publish-schedule.yaml'
REPORT = REPO / '.audit' / 'publish-schedule-validation.json'

source = json.loads(SOURCE.read_text(encoding='utf-8'))
source_items = source['schedule']
commit = subprocess.check_output(
    ['git', '-C', str(REPO), 'rev-parse', 'HEAD'], text=True
).strip()

errors: list[str] = []
warnings: list[str] = []
items: list[dict] = []

sequences = [entry.get('sequence') for entry in source_items]
expected_sequences = list(range(1, len(source_items) + 1))
if sequences != expected_sequences:
    errors.append('sequence 必須由 1 起連續遞增，且與清單順序一致')
if len(set(sequences)) != len(sequences):
    errors.append('sequence 存在重複值')

for entry in source_items:
    is_bonus = entry.get('system') == 'Bonus-Reuse'
    source_folder = entry['topic_folder']
    content_path = source_folder if is_bonus else f'content/{source_folder}'
    content_dir = REPO / content_path

    if not content_dir.is_dir():
        errors.append(f"sequence {entry['sequence']}: 內容資料夾不存在：{content_path}")

    declared_images = entry.get('images_present', [])
    media_paths = [f'{content_path}/{name}' for name in declared_images]
    missing_media = [path for path in media_paths if not (REPO / path).is_file()]
    if missing_media:
        errors.append(
            f"sequence {entry['sequence']}: 缺少素材：{', '.join(missing_media)}"
        )

    copy_candidates = []
    if content_dir.is_dir():
        copy_candidates = sorted(
            p for p in content_dir.iterdir()
            if p.is_file() and p.name.lower() in {'copy.md', 'copy.docx', 'copy.doc'}
        )
    copy_file = copy_candidates[0].relative_to(REPO).as_posix() if copy_candidates else None

    if entry.get('copy_ready') and not copy_file:
        errors.append(f"sequence {entry['sequence']}: copy_ready=true 但找不到 copy 檔")
    if not entry.get('copy_ready') and not copy_file:
        warnings.append(f"sequence {entry['sequence']}: 尚無可發布文案（符合目前狀態）")

    item = {
        'id': f"aquar-{entry['sequence']:03d}",
        'sequence': entry['sequence'],
        'week': entry['week'],
        'week_label': entry['week_label'],
        'system': entry['system'],
        'theme': entry['theme_cn'],
        'content_path': content_path,
        'copy': {
            'ready': bool(entry.get('copy_ready')),
            'file': copy_file,
        },
        'media': media_paths,
        'format': entry['format'],
        'tone': entry['tone'],
        'source_status': entry['status'],
        'release': {
            'enabled': False,
            'approval': 'pending',
            'publish_at': None,
            'buffer_mode': None,
        },
    }
    if entry.get('known_gap'):
        item['known_gap'] = entry['known_gap']
    if entry.get('needs_adaptation'):
        item['needs_adaptation'] = entry['needs_adaptation']
    items.append(item)

status_counts = dict(Counter(entry['status'] for entry in source_items))
week_counts = {
    int(week): count
    for week, count in sorted(Counter(entry['week'] for entry in source_items).items())
}

plan = {
    'schema_version': '1.0',
    'plan': {
        'name': 'Aquar social publishing order',
        'source_repository': source['repo'],
        'source_file': 'docs/publish-schedule-v2.json',
        'source_commit': commit,
        'timezone': 'Asia/Taipei',
        'mode': 'order_only',
        'publishing_enabled': False,
        'review_required': True,
        'timing': {
            'cadence': None,
            'start_at': None,
        },
        'order_basis': [
            'Week 1：破題喚醒',
            'Week 2：痛點共感',
            'Week 3：科學論證',
            'Week 4：品牌差異化',
            'Week 5：生活整合',
            'Week 6：長期陪伴收尾',
            'Week 7：延伸素材，預設不發布',
        ],
    },
    'delivery': {
        'strategy': 'undecided',
        'primary_channel': None,
        'facebook_delivery': None,
        'note': '待確認採 Buffer 直發 Facebook，或 Instagram 發布後由 Meta 跨貼；確認前保持停用。',
    },
    'counts': {
        'core': source['total_pieces_core'],
        'bonus': source['total_pieces_bonus'],
        'total': source['total_pieces'],
        'by_week': week_counts,
        'by_status': status_counts,
    },
    'items': items,
}

OUTPUT.write_text(
    yaml.safe_dump(plan, allow_unicode=True, sort_keys=False, width=1000),
    encoding='utf-8',
)

report = {
    'source_commit': commit,
    'source_entries': len(source_items),
    'yaml_entries': len(items),
    'sequences_contiguous': sequences == expected_sequences,
    'publishing_enabled': plan['plan']['publishing_enabled'],
    'release_enabled_count': sum(1 for item in items if item['release']['enabled']),
    'status_counts': status_counts,
    'week_counts': week_counts,
    'errors': errors,
    'warnings': warnings,
    'output': OUTPUT.relative_to(REPO).as_posix(),
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

print(json.dumps(report, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
