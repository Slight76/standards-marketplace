"""Unit tests for the shared standards tooling. Run: py -m unittest discover -s tooling/tests -v"""
from datetime import date
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check_adoption  # noqa: E402
import validate  # noqa: E402

CATALOGS = {
    'data-standards': {'version': '1.0.0', 'rules': [
        {'id': 'DB-001', 'status': 'Accepted'}, {'id': 'DB-002', 'status': 'Proposed'},
        {'id': 'OLD-001', 'status': 'Superseded'}]},
    'security-standards': {'version': '1.0.0', 'rules': [{'id': 'SEC-001', 'status': 'Accepted'}]},
}
SHA_A = 'a' * 40
SHA_B = 'b' * 40
TODAY = date(2026, 1, 15)


def baseline_v2():
    return {
        'schemaVersion': 2,
        'standards': [
            {'repository': 'https://github.com/Slight76/data-standards', 'revision': SHA_A, 'catalogVersion': '1.0.0'},
            {'repository': 'https://github.com/Slight76/security-standards', 'revision': SHA_B, 'catalogVersion': '1.0.0'},
        ],
        'solutionDocument': 'docs/solution-architecture.md',
        'applicationKind': 'backend',
        'adoptionRecord': {'owner': '@Slight76', 'date': '2026-01-10', 'evidence': 'PR #1'},
        'applicableRules': ['DB-001', 'SEC-001'],
        'excludedRules': [{'rule': 'DB-002', 'reason': 'No read replicas'}],
        'acceptedExceptions': [],
    }


def evidence_v2():
    return {
        'standards': [
            {'repository': 'https://github.com/Slight76/data-standards', 'revision': SHA_A},
            {'repository': 'https://github.com/Slight76/security-standards', 'revision': SHA_B},
        ],
        'applicationCommit': 'c' * 40,
        'checks': [
            {'rule': 'DB-001', 'status': 'passed', 'method': 'review', 'evidence': 'PR #2'},
            {'rule': 'SEC-001', 'status': 'not_run', 'reason': 'pending'},
        ],
    }


class AdoptionTests(unittest.TestCase):
    def check(self, baseline, evidence, **kw):
        return check_adoption.validate_adoption(CATALOGS, baseline, evidence, today=TODAY, **kw)

    def test_valid_v2(self):
        self.assertEqual(self.check(baseline_v2(), evidence_v2()), [])

    def test_v1_accepted_with_warning(self):
        b = {'standardsRepository': 'https://github.com/Slight76/data-standards', 'standardsRevision': SHA_A,
             'baselineVersion': '1.0.0', 'solutionDocument': 'docs/x.md', 'applicationKind': 'backend',
             'adoptionRecord': {'owner': 'o', 'date': '2026-01-10', 'evidence': 'e'},
             'applicableRules': ['DB-001'], 'excludedRules': [{'rule': 'DB-002', 'reason': 'r'}], 'acceptedExceptions': []}
        e = {'standardsRevision': SHA_A, 'baselineVersion': '1.0.0', 'applicationCommit': 'c' * 40,
             'checks': [{'rule': 'DB-001', 'status': 'passed', 'method': 'm', 'evidence': 'e'}]}
        warnings = []
        self.assertEqual(check_adoption.validate_adoption(CATALOGS, b, e, today=TODAY, warnings=warnings), [])
        self.assertTrue(any('deprecated' in w for w in warnings))

    def test_requires_immutable_revision(self):
        b = baseline_v2()
        b['standards'][0]['revision'] = 'main'
        self.assertTrue(any('40-character' in e for e in self.check(b, evidence_v2())))

    def test_catalog_version_mismatch(self):
        b = baseline_v2()
        b['standards'][1]['catalogVersion'] = '0.9.0'
        self.assertTrue(any('catalogVersion' in e for e in self.check(b, evidence_v2())))

    def test_missing_catalog(self):
        b = baseline_v2()
        b['standards'].append({'repository': 'https://github.com/Slight76/ops-standards', 'revision': SHA_A, 'catalogVersion': '1.0.0'})
        self.assertTrue(any('No catalog' in e for e in self.check(b, evidence_v2())))

    def test_coverage_mismatch_ignores_superseded(self):
        b = baseline_v2()
        b['applicableRules'].append('OLD-001')
        e = evidence_v2()
        e['checks'].append({'rule': 'OLD-001', 'status': 'not_applicable', 'reason': 'r'})
        self.assertTrue(any('Coverage mismatch' in x for x in self.check(b, e)))

    def test_evidence_pins_must_match(self):
        e = evidence_v2()
        e['standards'][0]['revision'] = 'd' * 40
        self.assertIn('Evidence standards pins differ from baseline', self.check(baseline_v2(), e))

    def test_require_pass_gate(self):
        self.assertTrue(any('Release gate' in e for e in self.check(baseline_v2(), evidence_v2(), require_pass=True)))

    def test_exception_coverage(self):
        b = baseline_v2()
        b['acceptedExceptions'] = [{'id': 'EXC-1', 'owner': 'o', 'approvalEvidence': 'a', 'reason': 'r', 'remediation': 'm',
                                    'status': 'Accepted', 'rules': ['SEC-001'], 'expires': '2027-01-01'}]
        e = evidence_v2()
        e['checks'][1] = {'rule': 'SEC-001', 'status': 'excepted', 'exceptionId': 'EXC-1'}
        self.assertEqual(self.check(b, e), [])
        e['checks'][1]['exceptionId'] = 'nope'
        self.assertTrue(any('covering accepted exception' in x for x in self.check(b, e)))

    def test_load_catalogs_from_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'data-standards' / 'catalog'
            root.mkdir(parents=True)
            (root / 'catalog.json').write_text(json.dumps(CATALOGS['data-standards']), encoding='utf-8')
            loaded = check_adoption.load_catalogs(baseline_v2(), Path(tmp))
            self.assertEqual(set(loaded), {'data-standards'})


def make_repo(root):
    """Minimal valid standards repository."""
    root = Path(root)
    (root / 'docs').mkdir(parents=True)
    (root / 'adr').mkdir()
    (root / 'catalog').mkdir()
    (root / 'skills' / 'demo-standards').mkdir(parents=True)
    (root / 'README.md').write_text('# Demo\n\nSee [doc](docs/demo.md).\n', encoding='utf-8')
    (root / 'AGENTS.md').write_text('# Agents\n\nRead skills/demo-standards/SKILL.md.\n', encoding='utf-8')
    (root / 'CLAUDE.md').write_text('@AGENTS.md\n', encoding='utf-8')
    (root / 'LICENSE').write_text('MIT\n', encoding='utf-8')
    (root / 'plugin.json').write_text(json.dumps({
        '$schema': 'https://agent-plugins.org/schemas/1.0.0/plugin.schema.json',
        'name': 'demo-standards', 'version': '1.0.0'}), encoding='utf-8')
    (root / 'skills' / 'demo-standards' / 'SKILL.md').write_text(
        '---\nname: demo-standards\ndescription: Demo skill.\n---\n# Demo\n', encoding='utf-8')
    (root / 'adr' / '0001-adopt.md').write_text(
        '# ADR-0001\n\nStatus: Accepted\n\n' + ''.join('## {}\n\nx\n\n'.format(h) for h in validate.ADR_HEADINGS),
        encoding='utf-8')
    (root / 'docs' / 'demo.md').write_text(
        '---\ntitle: Demo\nstatus: proposed\n---\n# Demo\n\n| ID | Requirement | Verification |\n|---|---|---|\n'
        '| DEMO-001 | Do it | Review |\n\nSee also EXT-001 and [ADR](../adr/0001-adopt.md).\n', encoding='utf-8')
    (root / 'catalog' / 'catalog.json').write_text(json.dumps({
        'version': '1.0.0',
        'externalDecisions': {'ADR-0002': {'repository': 'Slight76/architecture-standards', 'status': 'Accepted',
                                           'url': 'https://github.com/Slight76/architecture-standards/blob/main/adr/0002-x.md'}},
        'rules': [{'id': 'DEMO-001', 'domain': 'demo', 'statement': 's', 'verification': 'v', 'adr': 'ADR-0002',
                   'document': 'docs/demo.md', 'status': 'Accepted', 'applies_when': 'always'}]}), encoding='utf-8')
    (root / 'rule-index.json').write_text(json.dumps({'rules': [{'id': 'EXT-001'}]}), encoding='utf-8')
    return root


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = make_repo(self.tmp)
        self.index = self.root / 'rule-index.json'

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_validate(self):
        return validate.validate(self.root, self.index)

    def test_valid_repo(self):
        self.assertEqual(self.run_validate(), [])

    def test_unknown_rule_without_index(self):
        self.assertTrue(any('EXT-001' in e for e in validate.validate(self.root, None)))

    def test_broken_link(self):
        (self.root / 'README.md').write_text('[x](docs/missing.md)\n', encoding='utf-8')
        self.assertTrue(any('Broken link' in e for e in self.run_validate()))

    def test_enterprise_wording_rejected_outside_adr(self):
        doc = self.root / 'docs' / 'demo.md'
        doc.write_text(doc.read_text(encoding='utf-8') + '\nEnterprise rules apply.\n', encoding='utf-8')
        self.assertTrue(any('enterprise' in e for e in self.run_validate()))
        adr = self.root / 'adr' / '0001-adopt.md'
        adr.write_text(adr.read_text(encoding='utf-8') + '\nenterprise history\n', encoding='utf-8')
        self.assertFalse(any('enterprise' in e and 'adr/' in e for e in self.run_validate()))

    def test_superseded_rule_needs_successor(self):
        path = self.root / 'catalog/catalog.json'
        cat = json.loads(path.read_text(encoding='utf-8'))
        cat['rules'][0]['status'] = 'Superseded'
        path.write_text(json.dumps(cat), encoding='utf-8')
        self.assertTrue(any('names no successor rule' in e for e in self.run_validate()))
        cat['rules'][0]['superseded_by'] = 'GOV-001'
        path.write_text(json.dumps(cat), encoding='utf-8')
        self.assertFalse(any('successor' in e for e in self.run_validate()))

    def test_accepted_rule_requires_accepted_decision(self):
        path = self.root / 'catalog/catalog.json'
        cat = json.loads(path.read_text(encoding='utf-8'))
        cat['externalDecisions']['ADR-0002']['status'] = 'Proposed'
        path.write_text(json.dumps(cat), encoding='utf-8')
        self.assertTrue(any('non-accepted ADR' in e for e in self.run_validate()))

    def test_claude_must_import_agents(self):
        (self.root / 'CLAUDE.md').write_text('# nope\n', encoding='utf-8')
        self.assertIn('CLAUDE.md must start with @AGENTS.md', self.run_validate())

    def test_skill_name_must_match_directory(self):
        (self.root / 'skills/demo-standards/SKILL.md').write_text('---\nname: other\ndescription: d\n---\n', encoding='utf-8')
        self.assertTrue(any('name must match' in e for e in self.run_validate()))

    def test_doc_needs_frontmatter(self):
        (self.root / 'docs' / 'plain.md').write_text('# Plain\n', encoding='utf-8')
        self.assertTrue(any('lacks frontmatter' in e for e in self.run_validate()))


if __name__ == '__main__':
    unittest.main()
