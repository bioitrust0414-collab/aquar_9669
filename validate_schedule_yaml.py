#!/usr/bin/env python3
from pathlib import Path
import json
import yaml

repo = Path('/home/ubuntu/work/aquar_9669_current')
yaml_path = repo / '.audit' / 'publish-schedule.yaml'
data = yaml.safe_load(yaml_path.read_text(encoding='utf-8'))
items = data.get('items', [])
errors = []

if data.get('plan', {}).get('publishing_enabled') is not False:
    errors.append('全域 publishing_enabled 必須為 false')
if len(items) != 59:
    errors.append(f'項目數不是 59：{len(items)}')
if [item.get('sequence') for item in items] != list(range(1, 60)):
    errors.append('sequence 非 1–59 連續值')
if [item.get('id') for item in items] != [f'aquar-{i:03d}' for i in range(1, 60)]:
    errors.append('id 與 sequence 不一致')
if any(item.get('release', {}).get('enabled') is not False for item in items):
    errors.append('至少一筆 release.enabled 不是 false')

for item in items:
    if not (repo / item['content_path']).is_dir():
        errors.append(f"內容路徑不存在：{item['content_path']}")
    copy_file = item.get('copy', {}).get('file')
    if copy_file and not (repo / copy_file).is_file():
        errors.append(f'文案檔不存在：{copy_file}')
    for media in item.get('media', []):
        if not (repo / media).is_file():
            errors.append(f'媒體檔不存在：{media}')

result = {
    'yaml_parseable': True,
    'item_count': len(items),
    'all_release_disabled': not any(item['release']['enabled'] for item in items),
    'all_paths_resolve': not any('不存在' in error for error in errors),
    'errors': errors,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
if errors:
    raise SystemExit(1)
