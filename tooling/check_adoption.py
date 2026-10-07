"""Check declared baseline coverage/evidence shape; never attest runtime compliance.

Baseline schema v2 (architecture-baseline.json):

    {
      "schemaVersion": 2,
      "standards": [{"repository": "https://github.com/Slight76/data-standards",
                     "revision": "<40-char sha>", "catalogVersion": "1.0.0"}, ...],
      "solutionDocument": "docs/solution-architecture.md",
      "applicationKind": "backend",
      "adoptionRecord": {"owner": "...", "date": "YYYY-MM-DD", "evidence": "..."},
      "applicableRules": [...], "excludedRules": [...], "acceptedExceptions": [...]
    }

The v1 shape (standardsRepository/standardsRevision/baselineVersion) is still accepted with a
deprecation warning. Catalogs are read from --standards-dir/<repo-name>/catalog/catalog.json
(the layout produced by fetch_standards.py).

    py tooling/check_adoption.py --baseline architecture-baseline.json --evidence implementation-evidence.json
"""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys

SHA = re.compile(r'[0-9a-f]{40}')
REPO_URL = re.compile(r'https://[\w.-]+/[\w.-]+/([\w.-]+?)(?:\.git)?/?$')
STATUSES = {'passed', 'failed', 'not_run', 'not_applicable', 'excepted'}
KINDS = {'frontend', 'backend', 'worker', 'infrastructure', 'solution'}


def substantive(value):
    return isinstance(value, str) and bool(value.strip()) and not any(
        marker in value.upper() for marker in ('REPLACE', 'YYYY-MM-DD', 'TODO'))


def repo_name(url):
    match = REPO_URL.fullmatch(str(url or ''))
    return match.group(1) if match else None


def normalize_baseline(baseline, warnings):
    """Return (errors, standards) where standards is a list of {repository, revision, catalogVersion}."""
    errors = []
    if baseline.get('schemaVersion') == 2 or 'standards' in baseline:
        standards = baseline.get('standards')
        if not isinstance(standards, list) or not standards:
            return ['Baseline requires a non-empty standards array'], []
        for item in standards:
            if not isinstance(item, dict):
                errors.append('Each standards entry must be an object')
                continue
            if not repo_name(item.get('repository')):
                errors.append('standards entry requires an https repository URL')
            if not SHA.fullmatch(str(item.get('revision', ''))):
                errors.append('standards entry {} requires an immutable 40-character revision'.format(item.get('repository')))
            if not substantive(item.get('catalogVersion')):
                errors.append('standards entry {} requires catalogVersion'.format(item.get('repository')))
        names = [repo_name(s.get('repository')) for s in standards if isinstance(s, dict)]
        if len(set(names)) != len(names):
            errors.append('Duplicate standards repositories')
        return errors, [s for s in standards if isinstance(s, dict)]
    warnings.append('Baseline uses the deprecated v1 shape; migrate to schemaVersion 2 with a standards array')
    if not substantive(baseline.get('standardsRepository')):
        errors.append('Baseline requires standardsRepository')
    if not SHA.fullmatch(str(baseline.get('standardsRevision', ''))):
        errors.append('Baseline requires immutable 40-character standardsRevision')
    return errors, [{'repository': baseline.get('standardsRepository'), 'revision': baseline.get('standardsRevision'),
                     'catalogVersion': baseline.get('baselineVersion')}]


def validate_adoption(catalogs, baseline, evidence, require_pass=False, today=None, warnings=None):
    """catalogs: dict repo-name -> catalog dict (must cover every entry in the baseline)."""
    errors = []
    warnings = warnings if warnings is not None else []
    today = today or date.today()
    if not isinstance(baseline, dict) or not isinstance(evidence, dict):
        return ['Baseline and evidence must be objects']
    shape_errors, standards = normalize_baseline(baseline, warnings)
    errors.extend(shape_errors)
    known = set()
    for item in standards:
        name = repo_name(item.get('repository'))
        catalog = catalogs.get(name)
        if catalog is None:
            errors.append('No catalog available for {}'.format(item.get('repository')))
            continue
        if item.get('catalogVersion') != catalog.get('version'):
            errors.append('Baseline catalogVersion for {} does not match catalog {}'.format(name, catalog.get('version')))
        known |= {r['id'] for r in catalog['rules'] if r.get('status') != 'Superseded'}
    if not substantive(baseline.get('solutionDocument')):
        errors.append('Baseline requires solutionDocument')
    if baseline.get('applicationKind') not in KINDS:
        errors.append('Unknown applicationKind')
    record = baseline.get('adoptionRecord', {})
    if not isinstance(record, dict):
        record = {}
    for key in ('owner', 'date', 'evidence'):
        if not substantive(record.get(key)):
            errors.append('Adoption record requires {}'.format(key))
    try:
        if date.fromisoformat(record.get('date', '')) > today:
            errors.append('Adoption date cannot be in the future')
    except (ValueError, TypeError):
        errors.append('Adoption date must be YYYY-MM-DD')
    applicable = baseline.get('applicableRules', [])
    excluded = baseline.get('excludedRules', [])
    exceptions = baseline.get('acceptedExceptions', [])
    checks = evidence.get('checks', [])
    for name, collection in [('applicableRules', applicable), ('excludedRules', excluded),
                             ('acceptedExceptions', exceptions), ('checks', checks)]:
        if not isinstance(collection, list):
            errors.append('{} must be an array'.format(name))
    if not all(isinstance(x, list) for x in (applicable, excluded, exceptions, checks)):
        return errors
    if not all(isinstance(x, str) for x in applicable):
        return errors + ['applicableRules must contain rule IDs']
    if len(set(applicable)) != len(applicable):
        errors.append('Duplicate applicable rules')
    excluded_ids = []
    for item in excluded:
        if not isinstance(item, dict):
            errors.append('Each excluded rule must be an object')
            continue
        excluded_ids.append(item.get('rule'))
        if not substantive(item.get('reason')):
            errors.append('Excluded rule {} requires a reason'.format(item.get('rule')))
    if not all(isinstance(x, str) for x in excluded_ids):
        return errors + ['Excluded rule requires a rule ID']
    if len(set(excluded_ids)) != len(excluded_ids):
        errors.append('Duplicate excluded rules')
    declared = set(applicable) | set(excluded_ids)
    if set(applicable) & set(excluded_ids):
        errors.append('Rules cannot be both applicable and excluded')
    if known and declared != known:
        errors.append('Coverage mismatch: missing={}, unknown={}'.format(sorted(known - declared), sorted(declared - known)))
    exception_map = {}
    for item in exceptions:
        if not isinstance(item, dict):
            errors.append('Exception must be an object')
            continue
        eid = item.get('id')
        if not substantive(eid):
            errors.append('Exception requires an ID')
            continue
        if eid in exception_map:
            errors.append('Duplicate exception {}'.format(eid))
        exception_map[eid] = item
        for key in ('owner', 'approvalEvidence', 'reason', 'remediation'):
            if not substantive(item.get(key)):
                errors.append('Exception {} requires {}'.format(eid, key))
        if item.get('status') != 'Accepted':
            errors.append('Exception {} is not Accepted'.format(eid))
        rules = item.get('rules', [])
        if not isinstance(rules, list) or not rules or not all(isinstance(r, str) and r in applicable for r in rules):
            errors.append('Exception {} must name applicable rules'.format(eid))
        try:
            if date.fromisoformat(item.get('expires', '')) <= today:
                errors.append('Exception {} is expired'.format(eid))
        except (ValueError, TypeError):
            errors.append('Exception {} requires a valid expiry'.format(eid))
    # Evidence must pin exactly the same standards as the baseline.
    expected = sorted((repo_name(s.get('repository')) or '', str(s.get('revision'))) for s in standards)
    if 'standards' in evidence or baseline.get('schemaVersion') == 2:
        actual = sorted((repo_name(s.get('repository')) or '', str(s.get('revision')))
                        for s in evidence.get('standards', []) if isinstance(s, dict))
        if actual != expected:
            errors.append('Evidence standards pins differ from baseline')
    else:
        for key in ('standardsRevision', 'baselineVersion'):
            if evidence.get(key) != baseline.get(key):
                errors.append('Evidence {} differs from baseline'.format(key))
    if not SHA.fullmatch(str(evidence.get('applicationCommit', ''))):
        errors.append('Evidence requires a tested applicationCommit')
    seen = set()
    for check in checks:
        if not isinstance(check, dict):
            errors.append('Check must be an object')
            continue
        rid, status = check.get('rule'), check.get('status')
        if not isinstance(rid, str):
            errors.append('Check requires rule ID')
            continue
        if rid in seen:
            errors.append('Duplicate evidence for {}'.format(rid))
        seen.add(rid)
        if rid not in applicable:
            errors.append('Evidence for non-applicable rule {}'.format(rid))
        if status not in STATUSES:
            errors.append('Invalid status for {}'.format(rid))
        elif status == 'passed':
            if not substantive(check.get('method')) or not substantive(check.get('evidence')):
                errors.append('Passed rule {} requires method and evidence'.format(rid))
        elif status == 'excepted':
            ex = exception_map.get(check.get('exceptionId'), {})
            if rid not in ex.get('rules', []):
                errors.append('Rule {} lacks a covering accepted exception'.format(rid))
        elif not substantive(check.get('reason')):
            errors.append('Rule {} requires a reason for {}'.format(rid, status))
        if require_pass and status in {'failed', 'not_run'}:
            errors.append('Release gate: {} is {}'.format(rid, status))
    if seen != set(applicable):
        errors.append('Missing evidence for {}'.format(sorted(set(applicable) - seen)))
    return errors


def load_catalogs(baseline, standards_dir):
    """Load <standards_dir>/<repo-name>/catalog/catalog.json for every baseline entry."""
    catalogs = {}
    _, standards = normalize_baseline(baseline, [])
    for item in standards:
        name = repo_name(item.get('repository'))
        if not name:
            continue
        for candidate in (standards_dir / name / 'catalog/catalog.json', standards_dir / name / 'standards/catalog.json'):
            if candidate.is_file():
                catalogs[name] = json.loads(candidate.read_text(encoding='utf-8'))
                break
    return catalogs


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--evidence', required=True, type=Path)
    parser.add_argument('--standards-dir', default=Path('.standards'), type=Path,
                        help='directory holding one checkout per standards repository (default .standards)')
    parser.add_argument('--require-pass', action='store_true')
    args = parser.parse_args(argv)
    warnings = []
    try:
        baseline = json.loads(args.baseline.read_text(encoding='utf-8'))
        evidence = json.loads(args.evidence.read_text(encoding='utf-8'))
        catalogs = load_catalogs(baseline, args.standards_dir)
        errors = validate_adoption(catalogs, baseline, evidence, args.require_pass, warnings=warnings)
    except (OSError, ValueError, AttributeError) as exc:
        print('Cannot validate adoption: {}'.format(exc))
        return 1
    for warning in warnings:
        print('WARNING: {}'.format(warning))
    if errors:
        print('\n'.join(errors))
        return 1
    print('Declared adoption/evidence structure passed; runtime compliance is not attested.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
