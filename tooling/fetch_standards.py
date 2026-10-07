"""Clone every standards repository pinned in architecture-baseline.json at its exact revision.

    py tooling/fetch_standards.py --baseline architecture-baseline.json [--dest .standards]

Each repository is checked out into <dest>/<repo-name> in detached HEAD at the pinned 40-char
revision. Never use latest `main`; the baseline pin is the only trusted revision.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

SHA = re.compile(r'[0-9a-f]{40}')
REPO_URL = re.compile(r'https://[\w.-]+/[\w.-]+/([\w.-]+?)(?:\.git)?/?$')


def entries(baseline):
    if 'standards' in baseline:
        return [(s['repository'], s['revision']) for s in baseline['standards']]
    return [(baseline['standardsRepository'], baseline['standardsRevision'])]


def fetch(repo, revision, dest):
    name = REPO_URL.fullmatch(repo)
    if not name:
        raise ValueError('Unsupported repository URL: {}'.format(repo))
    if not SHA.fullmatch(str(revision)):
        raise ValueError('Revision for {} must be a 40-character commit SHA'.format(repo))
    target = dest / name.group(1)
    if not (target / '.git').is_dir():
        target.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'init', '-q'], cwd=target, check=True)
        subprocess.run(['git', 'remote', 'add', 'origin', repo], cwd=target, check=True)
    subprocess.run(['git', 'fetch', '-q', '--depth', '1', 'origin', revision], cwd=target, check=True)
    subprocess.run(['git', 'checkout', '-q', '--detach', revision], cwd=target, check=True)
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--baseline', default=Path('architecture-baseline.json'), type=Path)
    parser.add_argument('--dest', default=Path('.standards'), type=Path)
    args = parser.parse_args(argv)
    try:
        baseline = json.loads(args.baseline.read_text(encoding='utf-8'))
        for repo, revision in entries(baseline):
            target = fetch(repo, revision, args.dest)
            print('Fetched {} @ {} -> {}'.format(repo, revision[:12], target))
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('Cannot fetch standards: {}'.format(exc))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
