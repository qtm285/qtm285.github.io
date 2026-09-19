"""What must be true of the tree before it is published.

This is the only check that sees every change. `build-site.py` runs it while
assembling, but the assemble step is not how this site is usually updated: of
the last twelve commits touching `static/`, eleven changed between 1 and 28
files against a ~330-file regenerate, so they were published by hand. The
workflow step in `.github/workflows/pages.yml` runs this same function over the
committed tree, which is the one thing a hand-published change cannot go round.

Stdlib only, deliberately. It has to run on a GitHub runner that has none of
this project's dependencies, and it must not need the course source — the
runner checks out this repository and nothing else.
"""

from pathlib import Path

# Homework and exams are the pages that carry worked solutions. Skip's rule,
# 2026-09-18 05:31: "you guys know you're not to render solutions for students
# who've not yet handed in a hw assignment or at all on the static site, yes? /
# [like if you haven't submitted/are on the static site the chapter shows the
# like, handout version]".
SOLUTION_SECTIONS = ('homework', 'exams')

# The marker Quarto's solution callout leaves in rendered HTML.
SOLUTION_MARKER = 'callout-solution'


def pages_with_solutions(site_dir, book_subdir='book'):
  """Published chapter pages carrying worked solutions, worst first.

  A `*-solutions.html` page is exempt: that page *is* the solutions, and his own
  schedule links it once a homework is due.
  """
  site_dir = Path(site_dir)
  found = []
  for section in SOLUTION_SECTIONS:
    section_dir = site_dir / book_subdir / section
    if not section_dir.is_dir():
      continue
    for page in sorted(section_dir.glob('*.html')):
      if page.stem.endswith('-solutions'):
        continue
      blocks = page.read_text(errors='ignore').count(SOLUTION_MARKER)
      if blocks:
        found.append({'page': str(page.relative_to(site_dir)), 'blocks': blocks})
  return sorted(found, key=lambda row: -row['blocks'])


def read_allowlist(path):
  """Paths allowed to carry solutions, one per line; `#` comments ignored.

  The file is committed, so bypassing this check appears in the diff as an added
  line naming the page. That is the point: overriding is something a person
  chooses on the record, not something that happens.
  """
  path = Path(path)
  if not path.exists():
    return set()
  allowed = set()
  for line in path.read_text().splitlines():
    entry = line.split('#', 1)[0].strip()
    if entry:
      allowed.add(entry)
  return allowed


def solution_violations(site_dir, allowlist_path, book_subdir='book'):
  allowed = read_allowlist(allowlist_path)
  return [row for row in pages_with_solutions(site_dir, book_subdir)
          if row['page'] not in allowed]
