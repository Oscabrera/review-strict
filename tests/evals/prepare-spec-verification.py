#!/usr/bin/env python3
"""Prepare frozen synthetic spec inputs without exposing reference expected outcomes."""
import argparse
import hashlib
import json
from pathlib import Path
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--kind', choices=('spec', 'review'), default='spec')
a = p.parse_args()
name = 'spec-verification-cases.json' if a.kind == 'spec' else 'review-lessons-cases.json'
text_key, text_file = ('spec', 'spec.md') if a.kind == 'spec' else ('request', 'request.md')
data = json.loads(Path(__file__).with_name(name).read_text())
# Fail before writing if output exists or corpus is malformed.
assert not a.out.exists(), 'output must be a new directory'
assert len({c['id'] for c in data['cases']}) == len(data['cases'])
for c in data['cases']:
    assert c['id'].isdigit() and c[text_key] and c['source'] and c['expected']
a.out.mkdir(parents=True)
manifest = []
for c in data['cases']:
    d = a.out / c['id']; d.mkdir()
    (d/text_file).write_text(c[text_key]+('\n' if a.kind == 'spec' else ''))
    (d/'source.py').write_text(c['source'])
    digest = hashlib.sha256(((d/text_file).read_text()+(d/'source.py').read_text()).encode()).hexdigest()
    manifest.append({'id':c['id'], 'sha256':digest})
(a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(a.out)
