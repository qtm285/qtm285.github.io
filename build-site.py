from pathlib import Path
import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
from pybars import Compiler
import yaml

COURSE_DIR = None
SCHEDULE_SOURCE = None

# The schedule, from the book project
#
# The book's index.qmd holds the real schedule: date, title, the chapter each
# session links to, and the homework markers, in one markdown table. The landing
# page used to carry its own hand-typed copy, which is how the two came to
# disagree about which sessions are linked. This parses the book's table and
# generates the landing page's schedule from it, so there is one source.
#
# The link rule is Skip's: a session that has happened or is happening today
# links into the book; a future one is text. Applied here, at generation, so it
# is a consequence of the date rather than something anyone has to remember.

MONTHS = {m: i + 1 for i, m in enumerate(
  ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}

# `Th Aug 27`, or a range like `Dec 10-19` for an exam window. A range is the
# session's start: the window has begun once its first day has.
DATE_CELL = re.compile(r'^(?:(?P<weekday>M|T|W|Th|F|Sa|Su)\s+)?'
                       r'(?P<month>[A-Z][a-z]{2})\s+(?P<day>\d+)'
                       r'(?:\s*[-–—]\s*\d+)?$')

# A trailing `· *HW 1 due · HW 2 out*` is the homework markers for that session.
# The landing page gives each such group its own row under the session, so a
# session that puts two assignments out writes two groups and gets two rows.
# Anchored at the end so a whole-cell emphasis like `*No class (Fall Break)*` is
# not mistaken for a marker.
MARKER_GROUP = re.compile(r'\s*·\s*\*(?P<markers>[^*]+)\*\s*$')

MD_LINK = re.compile(r'\[(?P<text>[^\]]+)\]\((?P<target>[^)]+)\)')


def schedule_year(text):
  """The year the schedule's months belong to, from the document's own subtitle.

  Hardcoding it would go stale silently the first term nobody remembers to
  change it, and a wrong year makes every link decision wrong at once.
  """
  match = re.search(r'^subtitle:.*?(\d{4})', text, re.M)
  if match is None:
    raise ValueError(f'{SCHEDULE_SOURCE}: no year in the subtitle, so no schedule dates')
  return int(match.group(1))


def session_date(cell, year):
  match = DATE_CELL.match(cell.strip())
  if match is None:
    return None
  month = MONTHS.get(match.group('month'))
  if month is None:
    raise ValueError(f'{SCHEDULE_SOURCE}: unreadable month in date cell {cell!r}')
  # Aug-Dec is the fall term; a Jan-May row belongs to the spring that follows.
  return datetime.date(year if month >= 8 else year + 1, month, int(match.group('day')))


def dated_time(cell, time):
  return f'{cell.replace(" ", "&nbsp;")},&nbsp;{time}'


def meeting_date(cell):
  if cell.startswith(('T ', 'Th ')):
    return dated_time(cell, '4:00')
  if cell.startswith('F '):
    return dated_time(cell, '2:30')
  return cell.replace(' ', '&nbsp;')


def book_href(target):
  """Where something the schedule points at actually is on the site, or None.

  A `.qmd` is a chapter, and resolves to the book's rendered page if it is
  published — the same rule the homework list uses. Anything else is already a
  site asset, a handout zip in practice, and is passed through as written.

  Deliberately does not call `rendered()`: building the syllabus should not
  trigger a chapter render as a side effect.
  """
  if not target.endswith('.qmd'):
    return target
  href = Path('book') / Path(target).with_suffix('.html')
  return href if (ACTIVE_SITE / href).exists() else None


def cell_html(cell, linked):
  """One schedule cell as HTML. `linked` decides whether its chapter link survives.

  A future session keeps its title and loses its link, which is the whole rule.
  """
  def link(match):
    href = book_href(match.group('target')) if linked else None
    text = match.group('text')
    if not href:
      return text
    result = f'<a href="{href}">{text}</a>'
    target = Path(match.group('target'))
    deck = Path('decks') / f'{target.stem}-slides.html'
    if target.parts and target.parts[0] == 'chapters' and (ACTIVE_SITE / deck).exists():
      result += f' <a href="{deck}">[slides]</a>'
    return result

  # `\[` and `\]` are literal brackets around a link — the landing page writes
  # `[view]` with the brackets visible — so they must survive link substitution.
  html = MD_LINK.sub(link, cell.replace('\\[', '\0').replace('\\]', '\1'))
  html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html)
  html = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', html)
  return html.replace('·', '&middot;').replace('\0', '[').replace('\1', ']')


def declared_homeworks():
  config_text = (COURSE_DIR / '_quarto_book.yml').read_text()
  config = yaml.safe_load(config_text)
  result = []
  for part in config['book']['chapters']:
    for chapter in part.get('chapters', []) if isinstance(part, dict) else []:
      if chapter.startswith('homework/') and not chapter.endswith('.solutions.qmd'):
        result.append(COURSE_DIR / chapter)
  return iter(result)


def homework_html(path, number, linked):
  stem = path.stem.removesuffix('.handout')
  if not linked:
    return f'HW {number} out'
  page = Path('book/homework') / f'{stem}.html'
  archive = Path('book/homework/handouts') / f'{stem}-handout.zip'
  return (f'<a href="{page}">HW {number}</a> out '
          f'<a href="{archive}">[download zip]</a>')


def parse_schedule(today):
  """The book's schedule as `[(heading, [row, ...]), ...]`, dates already decided.

  A row that will not parse raises. Skipping it would drop a session off the
  syllabus silently, and nobody would find out until a student did.
  """
  text = SCHEDULE_SOURCE.read_text()
  year = schedule_year(text)
  if '## Schedule' not in text:
    raise ValueError(f'{SCHEDULE_SOURCE}: no "## Schedule" section to read')
  # Stop at the next top-level heading, or the practices and policies further
  # down the page contribute their own `###` headings as empty sections.
  body = re.split(r'^## (?!Schedule)', text.split('## Schedule', 1)[1], maxsplit=1, flags=re.M)[0]

  sections, heading, note, rows = [], None, None, []
  homework_paths = declared_homeworks()
  through_first_exam = False
  for line in body.splitlines():
    if through_first_exam:
      break
    if line.startswith('### '):
      if heading is not None:
        sections.append((heading, note, rows))
      heading, note, rows = line[4:].strip(), None, []
      continue
    if heading is None:
      continue
    # A sentence between the heading and the table qualifies the whole section --
    # "This unit is not on either exam." The landing page carried that inside the
    # heading, so dropping it here would quietly lose it.
    if not line.startswith('|'):
      if line.strip() and not rows:
        note = line.strip()
      continue
    cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
    if len(cells) != 2 or cells[0] in ('Date', '') or set(cells[0]) <= set('-: '):
      continue
    date = session_date(cells[0], year)
    if date is None:
      raise ValueError(f'{SCHEDULE_SOURCE}: unreadable date cell {cells[0]!r} — '
                       f'refusing to drop the session silently')
    main, markers = cells[1], []
    while True:
      match = MARKER_GROUP.search(main)
      if match is None:
        break
      markers.insert(0, match.group('markers'))
      main = main[:match.start()]
    homework = []
    for marker in markers:
      for event in re.finditer(r'\bHW\s+(?P<number>[−-]?\d+)\s+(?P<action>due|out)\b', marker):
        number, action = event.group('number'), event.group('action')
        if action == 'due':
          homework.append(f'HW {number} due')
        else:
          homework.append(homework_html(next(homework_paths), number, linked=date <= today))
    rows.append({'date': meeting_date(cells[0]),
                 'homework_date': dated_time(cells[0], '11:59'),
                 'session': cell_html(main, linked=date <= today),
                 'homework': homework})
    if main.strip() == '**Exam 1**':
      through_first_exam = True
  if heading is not None:
    sections.append((heading, note, rows))
  # A section whose table produced no rows means a table went unread -- a
  # different column count, a heading this loop did not recognise. Silently
  # covering half the term is worse than failing to build, and it is exactly
  # how the Part 2 rows were missed once already.
  empty = [h for h, _, r in sections if not r]
  if empty:
    raise ValueError(f'{SCHEDULE_SOURCE}: schedule sections with no rows parsed: '
                     f'{empty} -- a table was not read')
  return sections


def schedule_html(today=None):
  today = today or datetime.date.today()
  out = []
  for heading, note, rows in parse_schedule(today):
    out.append(f'<h5> {heading} </h5>\n')
    if note:
      out.append(f'<p>{cell_html(note, linked=False)}</p>\n')
    out.append('<table><tbody>')
    for row in rows:
      out.append(f'<tr><td>{row["date"]}</td><td> {row["session"]} </td></tr>')
      if row['homework']:
        out.append(f'<tr><td>{row["homework_date"]}</td><td> '
                   f'{" &middot; ".join(row["homework"])} </td></tr>')
    out.append('</tbody></table>\n')
  return '\n'.join(out)


# What the site says about itself
#
# The site used to carry no record of where it came from, so "is what's published
# current?" was a question only an agent with both trees in front of it could
# answer, and it was answered wrong: a tarball rendered at 15:39 from superseded
# source was published at 15:56 by a clean run. The three checks below all exist
# so that the assemble step refuses to do that, and `build-info.json` plus the
# line at the foot of the landing page exist so the answer is readable off the
# site itself rather than out of somebody's terminal.


def git_output(args):
  result = subprocess.run(['git', '-C', str(COURSE_DIR), *args], capture_output=True, text=True)
  if result.returncode != 0:
    raise ValueError(f'git {" ".join(args)} in {COURSE_DIR} failed: {result.stderr.strip()}')
  return result.stdout.strip()


def declared_chapters():
  """Every `.qmd` the book declares, whether or not it was rendered."""
  config = yaml.safe_load((COURSE_DIR / '_quarto_book.yml').read_text())
  result = []
  for part in config['book']['chapters']:
    entries = part.get('chapters', []) if isinstance(part, dict) else [part]
    for chapter in [entries] if isinstance(entries, str) else entries:
      if isinstance(chapter, str) and chapter.endswith('.qmd'):
        result.append(chapter)
  return result


def rendered_pages(book_dir):
  """The book's own record of what it rendered: `{output file: source file}`.

  Quarto leaves no revision behind, but the tlda manifest it writes alongside the
  pages maps each rendered page to the source it came from, which is what makes a
  per-page currency check possible at all.
  """
  manifest = book_dir / 'tlda-manifest.json'
  if not manifest.exists():
    raise ValueError(f'{manifest} is absent, so nothing records which source produced '
                     f'{book_dir} -- refusing to publish a tree whose currency cannot be checked')
  pages = json.loads(manifest.read_text())['pages']
  return {page['file']: page['source']['file']
          for page in pages if page.get('source', {}).get('file')}


def stale_pages(book_dir):
  """Pages whose source has been edited since the page was rendered.

  mtime is the only available oracle: neither `_book` nor `_freeze` records the
  revision a page was rendered from. It errs towards refusing -- touching a file
  without changing it raises the alarm -- which is the safe direction.
  """
  stale = []
  for page, source in sorted(rendered_pages(book_dir).items()):
    source_path, page_path = COURSE_DIR / source, book_dir / page
    if not source_path.exists() or not page_path.exists():
      continue
    rendered_at, edited_at = page_path.stat().st_mtime, source_path.stat().st_mtime
    if edited_at > rendered_at:
      stale.append({'page': page, 'source': source,
                    'renderedAt': stamp(rendered_at), 'sourceEditedAt': stamp(edited_at),
                    'behindMinutes': round((edited_at - rendered_at) / 60, 1)})
  return stale


def unbuilt_chapters(book_dir):
  built = set(rendered_pages(book_dir).values())
  return [chapter for chapter in declared_chapters() if chapter not in built]


def stamp(mtime):
  return datetime.datetime.fromtimestamp(mtime).astimezone().isoformat(timespec='seconds')


def course_provenance(book_dir):
  """Where the course source stood when this site was assembled."""
  sources = sorted(set(rendered_pages(book_dir).values()) | {'index.qmd', '_quarto_book.yml'})
  present = [source for source in sources if (COURSE_DIR / source).exists()]
  uncommitted = [line[3:] for line in
                 git_output(['status', '--porcelain=v1', '--', *present]).splitlines()]
  return {'checkout': str(COURSE_DIR),
          'revision': git_output(['rev-parse', 'HEAD']),
          'committedAt': git_output(['log', '-1', '--format=%cI']),
          'subject': git_output(['log', '-1', '--format=%s']),
          'uncommittedSources': uncommitted}


def site_files(root):
  return {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()}


def refuse_stale(book_dir, allowed):
  stale = stale_pages(book_dir)
  if stale and not allowed:
    rows = '\n'.join(f'  {row["page"]}\n'
                     f'    rendered      {row["renderedAt"]}\n'
                     f'    source edited {row["sourceEditedAt"]}  ({row["source"]}, '
                     f'{row["behindMinutes"]} min later)' for row in stale)
    raise SystemExit(f'{len(stale)} page(s) in {book_dir} are older than the source they '
                     f'were rendered from, so publishing would ship superseded work:\n{rows}\n'
                     f'Re-render the course, or pass --stale-ok to publish them anyway and say '
                     f'so on the site.')
  return stale


def refuse_unbuilt(book_dir, allowed):
  unbuilt = unbuilt_chapters(book_dir)
  if unbuilt and not allowed:
    rows = '\n'.join(f'  {chapter}' for chapter in unbuilt)
    raise SystemExit(f'{len(unbuilt)} chapter(s) that {COURSE_DIR / "_quarto_book.yml"} declares '
                     f'were never rendered into {book_dir}, so publishing would ship a partial '
                     f'book:\n{rows}\n'
                     f'Render them, or pass --incomplete-ok to publish without them and say so '
                     f'on the site.')
  return unbuilt


def refuse_deletions(stage_dir, site_dir, dropped, drop_all):
  """Nothing already published disappears because a fresh render did not carry it.

  The assemble step replaces the whole tree, so a render missing a handout zip or
  a deck deletes it from the site on an exit-zero run. That has happened: a
  regeneration from an out-of-sync `_book` staged 62 deletions including the
  homework setup handout students use.
  """
  if not site_dir.exists():
    return []
  going = sorted(site_files(site_dir) - site_files(stage_dir))
  if not going:
    return []
  if drop_all:
    return going
  unexpected = [path for path in going if path not in dropped]
  if unexpected:
    rows = '\n'.join(f'  {path}' for path in unexpected)
    raise SystemExit(f'{len(unexpected)} file(s) published in {site_dir} are absent from this '
                     f'build and would be deleted from the site:\n{rows}\n'
                     f'Re-render whatever produced them, or name each one with --drop, or pass '
                     f'--drop-all to remove all {len(going)}.')
  return going


def build_info(book_dir, provenance, stale, unbuilt, dropped):
  """What the site publishes about itself.

  This file is served, so it carries counts rather than paths for the same reason
  the stamp does: naming a page that was held back from the site announces it.
  The operator's copy, with every path, goes to stderr at the end of the run.
  """
  return {'version': 1,
          'builtAt': datetime.datetime.now().astimezone().isoformat(timespec='seconds'),
          'course': {'checkout': provenance['checkout'],
                     'revision': provenance['revision'],
                     'committedAt': provenance['committedAt'],
                     'subject': provenance['subject'],
                     'uncommittedSourceCount': len(provenance['uncommittedSources'])},
          'publishedStale': len(stale),
          'publishedWithoutChapters': len(unbuilt),
          'deletedFromSite': len(dropped)}


def build_stamp_html(info):
  """The one line on the landing page that answers "is this current?".

  Counts, never paths. This page is public, and a path here would announce the
  filename of material that was deliberately kept off the site -- homework that
  is still out, in practice. The operator gets the paths on stderr and in the
  refusal messages, which is where the evidence is useful anyway.

  Whatever was overridden to get the build out is still counted here, because a
  stamp that only ever reports success is not worth reading.
  """
  course = info['course']
  when = datetime.datetime.fromisoformat(info['builtAt']).strftime('%b %-d, %Y at %-I:%M %p')
  parts = [f'Built {when} from course revision '
           f'<code>{course["revision"][:12]}</code> ({course["subject"]}).']
  for count, description in (
      (course['uncommittedSourceCount'], 'source file(s) were uncommitted'),
      (info['publishedStale'], 'page(s) are older than the source they came from'),
      (info['publishedWithoutChapters'], 'declared chapter(s) are not in this build'),
      (info['deletedFromSite'], 'previously published file(s) were removed')):
    if count:
      parts.append(f'<b>{count}</b> {description}.')
  return ('<p style="margin-top:3em;font-size:0.8em;color:#666">'
          f'{" ".join(parts)}</p>')


def render_site(site_dir=Path('_site'), buildstamp=''):
  compiler = Compiler()
  source = open("index.template", "r").read()
  template = compiler.compile(source)
  output = template({
    'zoomlink': 'https://emory.zoom.us/j/91330426454?pwd=US7RfFmxBgGd2rvJCtnLcYu3zDepki.1',
    # add dummy element to count lectures/labs starting with 1
    'schedule': schedule_html(),
    'buildstamp': buildstamp
    })
  (site_dir / 'index.html').write_text(output)


def assemble_static(book_dir, site_dir, stale_ok=False, incomplete_ok=False,
                    dropped=(), drop_all=False):
  """Assemble the site beside the published one, check it, then swap.

  Staging first is what lets the deletion check compare the new tree against the
  published one while the published one still exists. The old order -- delete,
  then copy -- had already destroyed the evidence by the time anything could look.
  """
  global ACTIVE_SITE
  provenance = course_provenance(book_dir)
  stale = refuse_stale(book_dir, stale_ok)
  unbuilt = refuse_unbuilt(book_dir, incomplete_ok)

  stage_dir = site_dir.with_name(f'{site_dir.name}.staging')
  if stage_dir.exists():
    shutil.rmtree(stage_dir)
  # A refusal must leave nothing behind: a half-built tree sitting next to the
  # published one is another copy nobody can identify, and this repository is
  # published whole -- the deploy workflow uploads `path: .`.
  try:
    stage_dir.mkdir(parents=True)
    shutil.copytree(book_dir, stage_dir / 'book')
    for name in ('css', 'images'):
      shutil.copytree(Path('site-assets') / name, stage_dir / name)
    deck_dir = stage_dir / 'decks'
    deck_dir.mkdir()
    for html in (book_dir.parent / 'decks').glob('*-slides.html'):
      shutil.copy2(html, deck_dir / html.name)
      support = html.with_name(f'{html.stem}_files')
      if support.exists():
        shutil.copytree(support, deck_dir / support.name)

    info = build_info(book_dir, provenance, stale, unbuilt, [])
    (stage_dir / 'build-info.json').write_text(json.dumps(info, indent=2) + '\n')
    ACTIVE_SITE = stage_dir
    render_site(stage_dir, build_stamp_html(info))

    deleted = refuse_deletions(stage_dir, site_dir, set(dropped), drop_all)
    if deleted:
      info = build_info(book_dir, provenance, stale, unbuilt, deleted)
      (stage_dir / 'build-info.json').write_text(json.dumps(info, indent=2) + '\n')
      render_site(stage_dir, build_stamp_html(info))

    if site_dir.exists():
      shutil.rmtree(site_dir)
    stage_dir.rename(site_dir)
  except BaseException:
    ACTIVE_SITE = site_dir
    shutil.rmtree(stage_dir, ignore_errors=True)
    raise
  ACTIVE_SITE = site_dir
  # The operator's copy names every path. The published stamp and build-info.json
  # deliberately do not.
  summary = [f'{site_dir}: course revision {provenance["revision"][:12]}']
  for label, paths in (
      ('stale page(s) published', [row['page'] for row in stale]),
      ('declared chapter(s) not built', unbuilt),
      ('file(s) removed from the site', deleted),
      ('uncommitted source(s)', provenance['uncommittedSources'])):
    if paths:
      summary.append(f'  {len(paths)} {label}:')
      summary.extend(f'    {path}' for path in paths)
  print('\n'.join(summary), file=sys.stderr)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--course-dir', type=Path, required=True)
  parser.add_argument('--book-dir', type=Path)
  parser.add_argument('--site-dir', type=Path, default=Path('_site'))
  parser.add_argument('--stale-ok', action='store_true',
                      help='publish pages older than their source, and say so on the site')
  parser.add_argument('--incomplete-ok', action='store_true',
                      help='publish without chapters the book declares, and say so on the site')
  parser.add_argument('--drop', action='append', default=[], metavar='PATH',
                      help='a published file this build is meant to remove; repeatable')
  parser.add_argument('--drop-all', action='store_true',
                      help='remove every published file absent from this build')
  args = parser.parse_args()
  COURSE_DIR = args.course_dir.resolve()
  SCHEDULE_SOURCE = COURSE_DIR / 'index.qmd'
  ACTIVE_SITE = args.site_dir
  if args.book_dir:
    assemble_static(args.book_dir, args.site_dir, stale_ok=args.stale_ok,
                    incomplete_ok=args.incomplete_ok, dropped=args.drop, drop_all=args.drop_all)
  else:
    render_site(args.site_dir)
