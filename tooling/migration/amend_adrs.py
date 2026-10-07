"""One-off: amend historic ADRs in architecture-standards for the v1.0.0 split."""
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1])
ADR = ROOT / 'adr'
DATE = sys.argv[2]
NOTE = ('> Amended {d}: this record predates the v1.0.0 split. "Enterprise" wording is historical; the team-level '
        'operating model now lives in [standards-marketplace](https://github.com/Slight76/standards-marketplace/blob/main/governance/team-operating-model.md) '
        '(see [ADR-0028](0028-retire-enterprise-layer.md) and [ADR-0029](0029-split-into-domain-handbooks.md)).\n').format(d=DATE)


def rw(path, fn):
    text = path.read_text(encoding='utf-8')
    new = fn(text)
    path.write_text(new, encoding='utf-8', newline='\n') if sys.version_info >= (3, 10) else open(path, 'w', encoding='utf-8', newline='\n').write(new)


def supersede(text, successor, old_title, new_title):
    text = text.replace(old_title, new_title, 1)
    text = re.sub(r'^Status: .+$', 'Status: Superseded\n\nSuperseded by: ADR-{}'.format(successor), text, count=1, flags=re.M)
    return text


def amend(text):
    # Insert the note after the Date/Owner header block (before first '## ').
    idx = text.index('\n## ')
    return text[:idx] + '\n' + NOTE + text[idx:]


rw(ADR / '0001-enterprise.md', lambda t: amend(supersede(t, '0028', '# ADR-0001: Enterprise architecture', '# ADR-0001: Enterprise architecture (historical)')))
rw(ADR / '0023-implementation-decisions.md', lambda t: amend(supersede(t, '0028', '# ADR-0023: Measurable solution and enterprise ownership', '# ADR-0023: Measurable solution and enterprise ownership (historical)')))
for name in ['0002-solution', '0003-frontend', '0004-backend', '0005-database', '0006-integration', '0007-platform',
             '0008-infrastructure', '0009-security', '0010-independent-applications', '0011-agent-consumption',
             '0012-reference-technology-profile', '0022-implementation-decisions']:
    rw(ADR / (name + '.md'), amend)

# adr/README.md: fix de-enterprised link, mark superseded rows, add v1.0.0 section.
def readme(t):
    t = t.replace('[ADR-0001](0001-team.md) | Team architecture | Accepted', '[ADR-0001](0001-enterprise.md) | Enterprise architecture (historical) | Superseded by ADR-0028')
    t = t.replace('| Measurable solution and team ownership | Proposed', '| Measurable solution and ownership (historical) | Superseded by ADR-0028')
    t = t.replace('| ADR | Decision | Status |\n| --- | --- |\n', '| ADR | Decision | Status |\n| --- | --- | --- |\n')
    t += ('\n## Repository split decisions for v1.0.0\n\n'
          '| ADR | Decision | Status |\n| --- | --- | --- |\n'
          '| [ADR-0028](0028-retire-enterprise-layer.md) | Retire the enterprise layer; team operating model in standards-marketplace | Accepted |\n'
          '| [ADR-0029](0029-split-into-domain-handbooks.md) | Split into five domain handbooks plus a marketplace | Accepted |\n'
          '| [ADR-0030](0030-multi-repository-baseline.md) | Multi-repository baseline (`standards[]`, schema v2) | Accepted |\n'
          '| [ADR-0031](0031-skill-distribution.md) | Distribute handbooks as Agent Plugins skills via marketplace and gh skill | Accepted |\n\n'
          'Historic records keep their original wording; amendments are noted inline. Rule IDs are never renamed.\n')
    return t
rw(ADR / 'README.md', readme)
print('amended')
