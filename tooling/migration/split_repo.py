"""One-off migration: split architecture-standards v0.3.0 into six repositories.

Usage: py tooling/migration/split_repo.py --source <architecture-standards clone> --out <output root>

Writes <out>/<repo>/... for architecture-standards, engineering-standards, operations-standards,
data-standards, security-standards and standards-marketplace. Rewrites relative Markdown links
(same repo -> relative path, other repo -> GitHub blob URL), slices the rule catalog by document,
emits a cross-repo rule index and external-decision map, and removes "enterprise" framing.
"""
import argparse
import json
import posixpath
import re
import sys
from pathlib import Path

OWNER = 'Slight76'
SOURCE_SHA = 'c1bda3dde743c764027c80cd2aa2f9aae2f0e2e6'
ARCH, ENG, OPS, DATA, SEC, MP = ('architecture-standards', 'engineering-standards', 'operations-standards',
                                 'data-standards', 'security-standards', 'standards-marketplace')
REPOS = (ARCH, ENG, OPS, DATA, SEC, MP)
DOC_REPOS = (ARCH, ENG, OPS, DATA, SEC)

# old path -> (repo, new path)
MAP = {
    # architecture-standards (kept, restructured)
    'ARCHITECTURE-PRINCIPLES.md': (ARCH, 'ARCHITECTURE-PRINCIPLES.md'),
    'CHANGELOG.md': (ARCH, 'CHANGELOG.md'),
    'adr/README.md': (ARCH, 'adr/README.md'),
    'solution/architecture.md': (ARCH, 'docs/solution-architecture.md'),
    'solution/design-standard.md': (ARCH, 'docs/solution-design-standard.md'),
    'solution/examples/inventory.md': (ARCH, 'docs/examples/inventory.md'),
    'solution/examples/stock-adjustment.md': (ARCH, 'docs/examples/stock-adjustment.md'),
    'frontend/architecture.md': (ARCH, 'docs/frontend-architecture.md'),
    'frontend/accessibility-performance.md': (ARCH, 'docs/frontend-accessibility-performance.md'),
    'backend/architecture.md': (ARCH, 'docs/backend-architecture.md'),
    'backend/cqrs-standard.md': (ARCH, 'docs/cqrs-standard.md'),
    'backend/middleware-standard.md': (ARCH, 'docs/middleware-standard.md'),
    'backend/openapi-swagger-standard.md': (ARCH, 'docs/openapi-swagger-standard.md'),
    'integration/architecture.md': (ARCH, 'docs/integration-architecture.md'),
    'integration/contracts-standard.md': (ARCH, 'docs/contracts-standard.md'),
    'integration/http-api-standard.md': (ARCH, 'docs/http-api-standard.md'),
    'integration/messaging-resilience.md': (ARCH, 'docs/messaging-resilience.md'),
    'templates/solution-architecture.md': (ARCH, 'templates/solution-architecture.md'),
    'governance/migration-v0.2.md': (ARCH, 'governance/migration-v0.2.md'),
    'governance/migration-v0.3.md': (ARCH, 'governance/migration-v0.3.md'),
    # engineering-standards
    'governance/agent-development-standard.md': (ENG, 'docs/agent-development-standard.md'),
    'platform/testing-standard.md': (ENG, 'docs/testing-standard.md'),
    'backend/implementation-standard.md': (ENG, 'docs/backend-implementation-standard.md'),
    'frontend/implementation-standard.md': (ENG, 'docs/frontend-implementation-standard.md'),
    'governance/adoption.md': (ENG, 'docs/adoption-process.md'),
    # operations-standards
    'platform/architecture.md': (OPS, 'docs/platform-architecture.md'),
    'platform/delivery-standard.md': (OPS, 'docs/delivery-standard.md'),
    'platform/observability-standard.md': (OPS, 'docs/observability-standard.md'),
    'infrastructure/architecture.md': (OPS, 'docs/infrastructure-architecture.md'),
    'infrastructure/implementation-standard.md': (OPS, 'docs/infrastructure-implementation-standard.md'),
    'templates/operational-runbook.md': (OPS, 'templates/operational-runbook.md'),
    # data-standards
    'database/architecture.md': (DATA, 'docs/database-architecture.md'),
    'database/design-standard.md': (DATA, 'docs/design-standard.md'),
    'database/migration-recovery-standard.md': (DATA, 'docs/migration-recovery-standard.md'),
    'backend/persistence-standard.md': (DATA, 'docs/persistence-standard.md'),
    'backend/caching-standard.md': (DATA, 'docs/caching-standard.md'),
    # security-standards
    'security/architecture.md': (SEC, 'docs/security-architecture.md'),
    'security/application-security-standard.md': (SEC, 'docs/application-security-standard.md'),
    'security/cors-standard.md': (SEC, 'docs/cors-standard.md'),
    'security/identity-standard.md': (SEC, 'docs/identity-standard.md'),
    'templates/threat-model.md': (SEC, 'templates/threat-model.md'),
    # standards-marketplace (shared)
    'enterprise/operating-model.md': (MP, 'governance/team-operating-model.md'),
    'standards/technology-profile.md': (MP, 'standards/technology-profile.md'),
    'standards/sources.md': (MP, 'standards/sources.md'),
    'templates/adr.md': (MP, 'templates/adr.md'),
    'templates/exception.md': (MP, 'templates/exception.md'),
    'templates/implementation-evidence.md': (MP, 'templates/implementation-evidence.md'),
    'templates/implementation-evidence.json': (MP, 'templates/implementation-evidence.json'),
    'templates/agent-bootstrap.md': (MP, 'templates/agent-bootstrap.md'),
    'templates/architecture-baseline.json': (MP, 'templates/architecture-baseline.v1.json'),
    'consumer-kit/README.md': (MP, 'consumer-kit/README.md'),
    'consumer-kit/AGENTS.md.snippet': (MP, 'consumer-kit/AGENTS.md.snippet'),
    'consumer-kit/CLAUDE.md': (MP, 'consumer-kit/CLAUDE.md'),
    'consumer-kit/copilot-instructions.md': (MP, 'consumer-kit/copilot-instructions.md'),
    'consumer-kit/copilot-setup-steps.yml': (MP, 'consumer-kit/copilot-setup-steps.yml'),
    'scripts/check_adoption.py': (MP, 'tooling/check_adoption.py'),
    'scripts/fetch_standards.py': (MP, 'tooling/fetch_standards.py'),
    'scripts/validate.py': (MP, 'tooling/validate.py'),
    'tests/test_validation.py': (MP, 'tooling/tests/test_validation.py'),
}
# Deleted files and where links to them should point instead.
REDIRECT = {
    'enterprise/architecture.md': (MP, 'governance/team-operating-model.md'),
    'standards/README.md': (MP, 'README.md'),
    'standards/catalog.json': (MP, 'catalog/rule-index.json'),
    'README.md': (MP, 'README.md'),
    'AGENTS.md': (MP, 'README.md'),
    'CLAUDE.md': (MP, 'README.md'),
    'skills/architecture-standards/SKILL.md': (ARCH, 'skills/architecture-standards/SKILL.md'),
    'scripts/sync_skills.py': (MP, 'README.md'),
}

DE_ENTERPRISE = [
    (re.compile(r'\benterprise architecture standards\b', re.I), 'team architecture standards'),
    (re.compile(r'\bEnterprise architecture\b'), 'Team architecture'),
    (re.compile(r'\benterprise architecture\b'), 'team architecture'),
    (re.compile(r'\benterprise operating model\b', re.I), 'team operating model'),
    (re.compile(r'\benterprise rules\b'), 'team-level rules'),
    (re.compile(r'\benterprise-wide\b'), 'team-wide'),
    (re.compile(r'\benterprise ADR\b'), 'team-level ADR'),
    (re.compile(r'\bEnterprise\b'), 'Team'),
    (re.compile(r'\benterprise\b'), 'team'),
    (re.compile(r'Baseline: 0\.3\.0 recommended draft'), 'Baseline: 1.0.0'),
]
LINK = re.compile(r'(\[[^\]]*\]\()([^)\s]+)(\))')


def norm(path):
    return posixpath.normpath(path.replace('\\', '/'))


def resolve_target(old_path):
    """Return (repo, new_path) for an old repo-relative path, or None."""
    if old_path in MAP:
        return MAP[old_path]
    if old_path in REDIRECT:
        return REDIRECT[old_path]
    if re.fullmatch(r'adr/\d{4}-[\w.-]+\.md', old_path):
        return (ARCH, old_path)
    return None


def rewrite_links(text, old_path, new_repo, new_path, unresolved):
    old_dir = posixpath.dirname(old_path)
    new_dir = posixpath.dirname(new_path)

    def repl(m):
        link = m.group(2)
        if '://' in link or link.startswith(('#', 'mailto:')):
            return m.group(0)
        target, _, frag = link.partition('#')
        old_target = norm(posixpath.join(old_dir, target)) if target else old_path
        dest = resolve_target(old_target)
        if dest is None:
            unresolved.append((old_path, link))
            return m.group(0)
        repo, path = dest
        if repo == new_repo:
            rel = posixpath.relpath(path, new_dir or '.')
        else:
            rel = 'https://github.com/{}/{}/blob/main/{}'.format(OWNER, repo, path)
        return m.group(1) + rel + ('#' + frag if frag else '') + m.group(3)

    return LINK.sub(repl, text)


def de_enterprise(text):
    for pattern, replacement in DE_ENTERPRISE:
        text = pattern.sub(replacement, text)
    return text


def frontmatter(old_path, text):
    title = re.search(r'^# (.+)$', text, re.M)
    fm = ['---',
          'title: "{}"'.format(title.group(1).replace('"', "'") if title else old_path),
          'status: proposed',
          'version: 1.0.0',
          'owner: "@{}"'.format(OWNER),
          'supersedes: {}/{}@{}'.format(ARCH, old_path, SOURCE_SHA[:7]),
          '---', '']
    return '\n'.join(fm) + text


def write(out, repo, path, content, binary=False):
    dest = Path(out) / repo / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    if binary:
        dest.write_bytes(content)
    else:
        with dest.open('w', encoding='utf-8', newline='\n') as handle:
            handle.write(content)


def decision_ref(adr, decisions):
    return {'repository': '{}/{}'.format(OWNER, ARCH), 'status': decisions[adr][0],
            'url': 'https://github.com/{}/{}/blob/main/adr/{}'.format(OWNER, ARCH, decisions[adr][1])}


def split_catalog(source, out, decisions):
    catalog = json.loads((source / 'standards/catalog.json').read_text(encoding='utf-8'))
    per_repo = {r: [] for r in DOC_REPOS}
    superseded = []
    index = []
    for rule in catalog['rules']:
        doc = rule['document']
        if doc.startswith('enterprise/'):
            rule = dict(rule, status='Superseded', superseded_by='GOV-001',
                        document='governance/team-operating-model.md',
                        statement=de_enterprise(rule['statement']), applies_when=de_enterprise(rule['applies_when']),
                        note='Enterprise layer retired by ADR-0028; see standards-marketplace governance.')
            superseded.append(rule)
            index.append({'id': rule['id'], 'repository': MP, 'document': rule['document'], 'status': 'Superseded'})
            continue
        repo, new_path = MAP[doc]
        rule = dict(rule, document=new_path, statement=de_enterprise(rule['statement']),
                    applies_when=de_enterprise(rule['applies_when']))
        per_repo[repo].append(rule)
        index.append({'id': rule['id'], 'repository': repo, 'document': new_path, 'status': rule['status']})
    for repo, rules in per_repo.items():
        payload = {'version': '1.0.0', 'status': 'recommended-draft',
                   'repository': '{}/{}'.format(OWNER, repo), 'rules': rules}
        if repo != ARCH:
            payload['externalDecisions'] = {adr: decision_ref(adr, decisions) for adr in sorted({r['adr'] for r in rules})}
        write(out, repo, 'catalog/catalog.json', json.dumps(payload, indent=2) + '\n')
    gov_rule = {
        'id': 'GOV-001', 'domain': 'governance',
        'statement': 'Every application repository MUST declare the standards repositories and immutable revisions it adopts in architecture-baseline.json.',
        'verification': 'tooling/check_adoption.py passes against the declared baseline',
        'adr': 'ADR-0001', 'document': 'governance/team-operating-model.md', 'status': 'Proposed',
        'applies_when': 'a repository adopts any Slight76 standards handbook'}
    gov = {'version': '1.0.0', 'status': 'recommended-draft', 'repository': '{}/{}'.format(OWNER, MP),
           'rules': [gov_rule] + superseded,
           'externalDecisions': {adr: decision_ref(adr, decisions) for adr in sorted({r['adr'] for r in superseded})}}
    index.append({'id': 'GOV-001', 'repository': MP, 'document': 'governance/team-operating-model.md', 'status': 'Proposed'})
    write(out, MP, 'catalog/catalog.json', json.dumps(gov, indent=2) + '\n')
    write(out, MP, 'catalog/rule-index.json', json.dumps({
        'generatedFrom': '{}/{}@{}'.format(OWNER, ARCH, SOURCE_SHA),
        'rules': sorted(index, key=lambda r: r['id'])}, indent=2) + '\n')
    return {repo: len(rules) for repo, rules in per_repo.items()}, len(superseded)


def read_decisions(source):
    decisions = {}
    for path in sorted((source / 'adr').glob('[0-9][0-9][0-9][0-9]-*.md')):
        text = path.read_text(encoding='utf-8')
        status = re.search(r'^Status: (.+)$', text, re.M)
        decisions['ADR-' + path.name[:4]] = (status.group(1).strip() if status else 'Proposed', path.name)
    return decisions


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    source, out = args.source, args.out
    unresolved = []
    for old_path, (repo, new_path) in MAP.items():
        src = source / old_path
        if not src.is_file():
            print('missing source file:', old_path)
            continue
        if old_path.endswith('.md') or old_path.endswith('.snippet'):
            text = src.read_text(encoding='utf-8')
            text = rewrite_links(text, old_path, repo, new_path, unresolved)
            text = de_enterprise(text)
            if new_path.startswith('docs/') and repo in DOC_REPOS:
                text = frontmatter(old_path, text)
            write(out, repo, new_path, text)
        else:
            write(out, repo, new_path, src.read_bytes(), binary=True)
    for path in sorted((source / 'adr').glob('[0-9][0-9][0-9][0-9]-*.md')):
        old_path = 'adr/' + path.name
        text = rewrite_links(path.read_text(encoding='utf-8'), old_path, ARCH, old_path, unresolved)
        write(out, ARCH, old_path, text)  # ADR wording is amended by hand to preserve history
    decisions = read_decisions(source)
    counts, retired = split_catalog(source, out, decisions)
    print('rules per repo:', counts, '| retired EA rules:', retired)
    if unresolved:
        print('UNRESOLVED LINKS:')
        for item in unresolved:
            print('  ', item)
        return 1
    print('ok')
    return 0


if __name__ == '__main__':
    sys.exit(main())
