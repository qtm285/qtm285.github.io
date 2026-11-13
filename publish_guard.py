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
import html
import re

# Homework and exams are the pages that carry worked solutions. Skip's rule,
# 2026-09-18 05:31: "you guys know you're not to render solutions for students
# who've not yet handed in a hw assignment or at all on the static site, yes? /
# [like if you haven't submitted/are on the static site the chapter shows the
# like, handout version]".
SOLUTION_SECTIONS = ('homework', 'exams')

# The marker Quarto's solution callout leaves in rendered HTML: the class on
# the callout element itself. A script that only names the selector (the
# reader bridge does) is not a solution block.
SOLUTION_MARKER = re.compile(r'''class=["'][^"']*\bcallout-solution\b''')


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
      blocks = len(SOLUTION_MARKER.findall(page.read_text(errors='ignore')))
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


HTML_TAG = re.compile(r'<[^>]+>')
HW_NUMBERED_OUT_DUE = re.compile(r'(?<![−-])\bHW\s+(\d+)\s+(out|due)\b')
HW_ANY_MENTION = re.compile(r'\bHW\s*[-−]?\d+\b')
HOMEWORK_HREF = re.compile(r'href=["\'](?:book/)?(homework/homework-[^"\'#?]+\.html)["\']')


def _plain_text(fragment):
  return ' '.join(html.unescape(HTML_TAG.sub(' ', fragment)).replace('\u00a0', ' ').split())


def schedule_violations_html(landing_html, book_html=None):
  """Check rendered landing and book index HTML for nonstandard schedule edits.

  Enforces three structural invariants on the published schedule:
  1. Each ``Part`` section renders as exactly one continuous ``<table>`` (no
     mid-section notes splitting a Part into multiple tables).
  2. No prose ``<p>`` inside a schedule section announces or links homework.
  3. Every numbered homework ``HW N`` (``N >= 0``) and every linked assignment
     page ``homework/homework-*.html`` (excluding ``homework-setup.html`` and
     ``*-solutions.html``) sits on a ``11:59`` landing-page row with both
     ``HW N out`` and a subsequent ``HW N due`` row.
  """
  issues = []
  match = re.search(
      r'<div class="row" id="schedule">(.*?)<div class="row" id="practices">',
      landing_html, re.S)
  if match is None:
    issues.append('static/index.html: missing #schedule .. #practices region')
  else:
    sched = match.group(1)
    if '\\<em' in sched or '\\</em' in sched or '\\*' in sched:
      issues.append(
          'static/index.html: literal backslash-asterisk escaping artifact in #schedule')
    parts = re.split(r'(<h5>.*?</h5>)', sched, flags=re.S)
    if len(parts) < 3:
      issues.append('static/index.html: no <h5> Part headings inside #schedule')
    for idx in range(1, len(parts), 2):
      heading = _plain_text(parts[idx])
      body = parts[idx + 1]
      tables = re.findall(r'<table\b[^>]*>.*?</table>', body, flags=re.S)
      if len(tables) != 1:
        issues.append(
            f'static/index.html: section {heading!r} has {len(tables)} <table> '
            f'element(s); expected exactly 1 continuous schedule table')
      for p_html in re.findall(r'<p\b[^>]*>.*?</p>', body, flags=re.S):
        p_txt = _plain_text(p_html)
        if 'homework/' in p_html or HW_ANY_MENTION.search(p_txt):
          issues.append(
              f'static/index.html: prose paragraph inside {heading!r} announces '
              f'homework outside the schedule table: {p_txt!r}')

    hw_out = {}
    hw_due = {}
    row_pos = 0
    for tr in re.findall(r'<tr\b[^>]*>(.*?)</tr>', sched, flags=re.S):
      tds = re.findall(r'<td\b[^>]*>(.*?)</td>', tr, flags=re.S)
      if len(tds) != 2:
        continue
      row_pos += 1
      dt, raw_cell = _plain_text(tds[0]), tds[1]
      txt = _plain_text(raw_cell)
      if re.search(r'\[\s*solutions\s*\]', raw_cell):
        issues.append(
            f'static/index.html: unlinked "[solutions]" bracket on {dt!r}')
      is_hw_row = dt.endswith(', 11:59')
      for href in HOMEWORK_HREF.findall(raw_cell):
        if href.endswith('-solutions.html') or href == 'homework/homework-setup.html':
          continue
        if not is_hw_row or not HW_NUMBERED_OUT_DUE.search(txt):
          issues.append(
              f'static/index.html: {href!r} on {dt!r} is not on a standard '
              f'11:59 "HW N out" row')
      for m_hw in HW_NUMBERED_OUT_DUE.finditer(txt):
        num = int(m_hw.group(1))
        role = m_hw.group(2)
        if not is_hw_row:
          issues.append(
              f'static/index.html: "HW {num} {role}" on {dt!r} sits on a class '
              f'row instead of a 11:59 assignment row')
        (hw_out if role == 'out' else hw_due).setdefault(num, []).append((row_pos, dt))

    for num in sorted(set(hw_out) | set(hw_due)):
      outs = hw_out.get(num, [])
      dues = hw_due.get(num, [])
      if len(outs) != 1:
        issues.append(
            f'static/index.html: HW {num} has {len(outs)} "HW {num} out" row(s); expected 1')
      if len(dues) != 1:
        issues.append(
            f'static/index.html: HW {num} has {len(dues)} "HW {num} due" row(s); '
            f'expected 1 (every posted homework must list its due date)')
      if len(outs) == 1 and len(dues) == 1 and dues[0][0] <= outs[0][0]:
        issues.append(
            f'static/index.html: HW {num} due ({dues[0][1]}) must appear after '
            f'HW {num} out ({outs[0][1]})')

  if book_html is not None:
    mb = re.search(
        r'<section id="schedule"[^>]*>(.*?)</section>\s*<section id="class-practices"',
        book_html, re.S)
    if mb is None:
      issues.append('static/book/index.html: missing #schedule .. #class-practices section')
    else:
      bsched = mb.group(1)
      if '\\<em' in bsched or '\\</em' in bsched or '\\*' in bsched:
        issues.append(
            'static/book/index.html: literal backslash-asterisk escaping artifact in #schedule')
      if re.search(r'\[\s*solutions\s*\]', bsched):
        issues.append(
            'static/book/index.html: unlinked "[solutions]" bracket in #schedule')
      l3s = re.findall(r'<section id="part-[^"]*" class="level3">(.*?)</section>', bsched, re.S)
      if not l3s:
        issues.append('static/book/index.html: no Part level3 sections in #schedule')
      for l3 in l3s:
        h3_m = re.search(r'<h3[^>]*>(.*?)</h3>', l3, re.S)
        h3 = _plain_text(h3_m.group(1)) if h3_m else 'Part'
        if '<ul' in l3:
          issues.append(
              f'static/book/index.html: unintended <ul> bullet list in {h3!r} (escape leading "*")')
        tables = re.findall(r'<table\b[^>]*>.*?</table>', l3, flags=re.S)
        if len(tables) != 1:
          issues.append(
              f'static/book/index.html: section {h3!r} has {len(tables)} <table> '
              f'element(s); expected exactly 1')
        for p_html in re.findall(r'<p\b[^>]*>.*?</p>', l3, flags=re.S):
          p_txt = _plain_text(p_html)
          if 'homework/' in p_html or HW_ANY_MENTION.search(p_txt):
            issues.append(
                f'static/book/index.html: prose paragraph inside {h3!r} announces '
                f'homework outside the schedule table: {p_txt!r}')
  return issues


def schedule_violations(site_dir, book_subdir='book'):
  site_dir = Path(site_dir)
  landing_path = site_dir / 'index.html'
  if not landing_path.is_file():
    return [f'{landing_path} is missing']
  landing_html = landing_path.read_text(encoding='utf8', errors='ignore')
  book_path = site_dir / book_subdir / 'index.html'
  book_html = book_path.read_text(encoding='utf8', errors='ignore') if book_path.is_file() else None
  return schedule_violations_html(landing_html, book_html)
