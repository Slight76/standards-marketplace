"""Validate a standards repository: catalog, ADRs, documents, links, JSON, agent files.

Runs against any Slight76 *-standards repository (or standards-marketplace itself):

    py tooling/validate.py --root ../data-standards [--rule-index catalog/rule-index.json]

No runtime compliance claims are made; this checks documentation integrity only.
"""
import argparse
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
MARKETPLACE_ROOT = HERE.parent
RULE = re.compile(r'\b[A-Z]+-\d{3}\b')
ADR_ID = re.compile(r'ADR-\d{4}')
ADR_STATUSES = {'Accepted', 'Proposed', 'Rejected', 'Superseded'}
RULE_STATUSES = {'Accepted', 'Proposed', 'Superseded'}
ADR_HEADINGS = ('Context', 'Decision', 'Alternatives', 'Consequences', 'Traceability', 'Verification', 'Approval')
REQUIRED_FILES = ('README.md', 'AGENTS.md', 'CLAUDE.md', 'LICENSE', 'plugin.json', 'catalog/catalog.json')
# Historic "enterprise" wording may remain only in these paths.
ENTERPRISE_ALLOWED = ('adr/', 'CHANGELOG.md', 'MOVED.md', 'catalog/', 'governance/migration-')
# Directories never validated: VCS data, the scaffold template, and checkouts made by CI/consumers.
SKIP_DIRS = ('.git/', 'scaffold/', '.marketplace/', '.standards/', 'node_modules/')
ENTERPRISE = re.compile(r'\benterprise\b', re.I)


def is_relative_to(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read(path):
    return path.read_text(encoding='utf-8-sig')


def local_decisions(root, errors):
    decisions = {}
    for path in sorted((root / 'adr').glob('[0-9][0-9][0-9][0-9]-*.md')):
        text = read(path)
        aid = 'ADR-' + path.name[:4]
        if aid in decisions:
            errors.append('Duplicate ADR {}'.format(aid))
        status = re.search(r'^Status: (.+)$', text, re.M)
        decisions[aid] = status.group(1).strip() if status else None
        for heading in ADR_HEADINGS:
            if '## {}'.format(heading) not in text:
                errors.append('{} lacks {}'.format(aid, heading))
        if decisions[aid] not in ADR_STATUSES:
            errors.append('{} has invalid status'.format(aid))
        if decisions[aid] == 'Superseded' and not re.search(r'^Superseded by: ADR-\d{4}', text, re.M):
            errors.append('{} is Superseded but names no successor'.format(aid))
    return decisions


def validate_catalog(root, catalog, decisions, errors):
    external = catalog.get('externalDecisions', {})
    for aid, ref in external.items():
        if not ADR_ID.fullmatch(aid) or ref.get('status') not in ADR_STATUSES or not str(ref.get('url', '')).startswith('https://'):
            errors.append('Invalid externalDecisions entry {}'.format(aid))
        decisions.setdefault(aid, ref.get('status'))
    seen = set()
    for rule in catalog['rules']:
        rid = rule.get('id', '')
        if not RULE.fullmatch(rid) or rid in seen:
            errors.append('Invalid/duplicate rule {}'.format(rid))
        seen.add(rid)
        for key in ('domain', 'statement', 'verification', 'adr', 'document', 'status', 'applies_when'):
            if not isinstance(rule.get(key), str) or not rule[key].strip():
                errors.append('{} missing {}'.format(rid, key))
        doc = (root / rule['document']).resolve()
        if not is_relative_to(doc, root.resolve()) or not doc.is_file():
            errors.append('{} has invalid document'.format(rid))
        elif rule['status'] != 'Superseded' and not re.search(r'\|\s*' + re.escape(rid) + r'\s*\|', read(doc)):
            errors.append('{} missing from document rule table'.format(rid))
        if rule['adr'] not in decisions:
            errors.append('{} references unknown ADR'.format(rid))
        if rule['status'] not in RULE_STATUSES:
            errors.append('{} has invalid status'.format(rid))
        if rule['status'] == 'Accepted' and decisions.get(rule['adr']) != 'Accepted':
            errors.append('{} cannot be Accepted under a non-accepted ADR'.format(rid))
        if rule['status'] == 'Superseded' and not RULE.fullmatch(str(rule.get('superseded_by', ''))):
            errors.append('{} is Superseded but names no successor rule'.format(rid))
    return seen


def validate_documents(root, known, errors):
    for doc in root.rglob('*.md'):
        rel = doc.relative_to(root).as_posix()
        if rel.startswith(SKIP_DIRS):
            continue
        text = read(doc)
        for link in re.findall(r'\[[^\]]*\]\(([^)\s]+)\)', text):
            if '://' in link or link.startswith(('#', 'mailto:')):
                continue
            target = (doc.parent / link.split('#')[0]).resolve()
            if not is_relative_to(target, root.resolve()) or not target.exists():
                errors.append('Broken link: {} -> {}'.format(rel, link))
        for rid in RULE.findall(text):
            if rid not in known:
                errors.append('Unknown rule mention {} in {}'.format(rid, rel))
        if rel.startswith('docs/') and not text.startswith('---\n'):
            errors.append('{} lacks frontmatter'.format(rel))
        body = re.sub(r'\A---\n.*?\n---\n', '', text, count=1, flags=re.S)
        if not rel.startswith(ENTERPRISE_ALLOWED) and ENTERPRISE.search(body):
            errors.append('"enterprise" wording in {} (retired by ADR-0028)'.format(rel))


def validate_agent_files(root, errors):
    for name in REQUIRED_FILES:
        if not (root / name).is_file():
            errors.append('Missing required file: {}'.format(name))
    if errors:
        return
    if not read(root / 'CLAUDE.md').lstrip().startswith('@AGENTS.md'):
        errors.append('CLAUDE.md must start with @AGENTS.md')
    plugin = load_json(root / 'plugin.json')
    if plugin.get('$schema') != 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json':
        errors.append('plugin.json must declare the Agent Plugins 1.0 schema')
    if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', str(plugin.get('name', ''))) or '--' in plugin.get('name', ''):
        errors.append('plugin.json name must be lowercase kebab-case')
    skills = list((root / 'skills').glob('*/SKILL.md'))
    if not skills:
        errors.append('No skills/*/SKILL.md found')
    for skill in skills:
        text = read(skill)
        match = re.match(r'---\n(.*?)\n---\n', text, re.S)
        if not match:
            errors.append('{} lacks frontmatter'.format(skill.relative_to(root).as_posix()))
            continue
        name = re.search(r'^name: (.+)$', match.group(1), re.M)
        desc = re.search(r'^description: (.+)$', match.group(1), re.M)
        if not name or name.group(1).strip() != skill.parent.name:
            errors.append('{} name must match its directory'.format(skill.relative_to(root).as_posix()))
        if not desc or len(desc.group(1)) > 1024:
            errors.append('{} needs a description of at most 1024 characters'.format(skill.relative_to(root).as_posix()))
        if text.count('\n') > 500:
            errors.append('{} exceeds 500 lines'.format(skill.relative_to(root).as_posix()))
    for file in root.rglob('*.json'):
        if file.relative_to(root).as_posix().startswith(SKIP_DIRS):
            continue
        try:
            load_json(file)
        except ValueError:
            errors.append('Invalid JSON: {}'.format(file.relative_to(root).as_posix()))


def validate(root, rule_index=None):
    root = Path(root)
    errors = []
    catalog = load_json(root / 'catalog/catalog.json')
    decisions = local_decisions(root, errors)
    known = validate_catalog(root, catalog, decisions, errors)
    if rule_index and Path(rule_index).is_file():
        known |= {r['id'] for r in load_json(Path(rule_index))['rules']}
    validate_documents(root, known, errors)
    validate_agent_files(root, errors)
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.', type=Path)
    parser.add_argument('--rule-index', default=MARKETPLACE_ROOT / 'catalog/rule-index.json', type=Path)
    args = parser.parse_args(argv)
    try:
        errors = validate(args.root, args.rule_index)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print('Document validation error: {}'.format(exc))
        return 1
    if errors:
        print('\n'.join(errors))
        return 1
    catalog = load_json(Path(args.root) / 'catalog/catalog.json')
    print('Validated {} rules, ADR consistency, JSON, agent files, and local document links in {}.'.format(
        len(catalog['rules']), Path(args.root).resolve().name))
    return 0


if __name__ == '__main__':
    sys.exit(main())
