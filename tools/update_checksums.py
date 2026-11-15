#!/usr/bin/env python3
"""Run only when intentionally regenerating/reviewing bundled assets."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
data={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(list((root/'assets/scenes').glob('*/*'))+[root/'assets/remote.json']) if p.is_file()}
(root/'assets/checksums.json').write_text(json.dumps(data,indent=2)+'\n')
print(f'{len(data)} asset hashes updated')
