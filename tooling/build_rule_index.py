"""Rebuild catalog/rule-index.json from sibling handbook checkouts.

    py tooling/build_rule_index.py [--repos-dir ..]

Expects each Slight76 standards repository cloned next to this one. Fails on duplicate rule IDs.
"""
import argparse
import collections
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REPOS = ('architecture-standards', 'engineering-standards', 'operations-standards',
         'data-standards', 'security-standards', 'standards-marketplace')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repos-dir', default=HERE.parent.parent, type=Path)
    args = parser.parse_args(argv)
    rules, seen, versions = [], collections.Counter(), {}
    for repo in REPOS:
        path = args.repos_dir / repo / 'catalog' / 'catalog.json'
        catalog = json.loads(path.read_text(encoding='utf-8-sig'))
        versions[repo] = catalog['version']
        for rule in catalog['rules']:
            seen[rule['id']] += 1
            rules.append({'id': rule['id'], 'repository': 'Slight76/' + repo, 'document': rule['document'],
                          'status': rule['status'], 'catalogVersion': catalog['version']})
    dups = sorted(k for k, v in seen.items() if v > 1)
    if dups:
        print('Duplicate rule IDs across handbooks: {}'.format(dups))
        return 1
    index = {'version': '1.0.0', 'generated_from': versions, 'rules': sorted(rules, key=lambda r: r['id'])}
    out = HERE.parent / 'catalog' / 'rule-index.json'
    with out.open('w', encoding='utf-8', newline='\n') as handle:
        json.dump(index, handle, indent=2)
        handle.write('\n')
    print('Wrote {} rules to {}'.format(len(rules), out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
