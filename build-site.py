from pathlib import Path
import argparse
import datetime
import re
import shutil
from pybars import Compiler
import yaml

COURSE_DIR = None
SCHEDULE_SOURCE = None

# Homework that has not come out yet, collected while the schedule is read.
#
# Leaving a future homework's page unlinked is not the same as not publishing
# it: the book build renders every declared chapter, the site copies the book
# wholesale, and the page then answers on its URL with the solutions inside it.
# On 2026-09-18 HW3's and HW4's worked solutions were served that way while both
# were still out. Unlinked is not unposted, so these are removed from the
# assembled site, on the same date rule that decides the linking.
WITHHELD_HOMEWORK = []

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
    # The schedule is read more than once per build, so guard against listing
    # the same homework twice: a doubled "withheld" line reads as two removals.
    if stem not in WITHHELD_HOMEWORK:
      WITHHELD_HOMEWORK.append(stem)
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


def render_site(site_dir=Path('_site')):
  compiler = Compiler()
  source = open("index.template", "r").read()
  template = compiler.compile(source)
  output = template({
    'zoomlink': 'https://emory.zoom.us/j/91330426454?pwd=US7RfFmxBgGd2rvJCtnLcYu3zDepki.1',
    # add dummy element to count lectures/labs starting with 1
    'schedule': schedule_html()
    })
  (site_dir / 'index.html').write_text(output)


def assemble_static(book_dir, site_dir):
  global ACTIVE_SITE
  if site_dir.exists():
    shutil.rmtree(site_dir)
  site_dir.mkdir(parents=True)
  shutil.copytree(book_dir, site_dir / 'book')
  for name in ('css', 'images'):
    shutil.copytree(Path('site-assets') / name, site_dir / name)
  deck_dir = site_dir / 'decks'
  deck_dir.mkdir()
  for html in (book_dir.parent / 'decks').glob('*-slides.html'):
    shutil.copy2(html, deck_dir / html.name)
    support = html.with_name(f'{html.stem}_files')
    if support.exists():
      shutil.copytree(support, deck_dir / support.name)
  ACTIVE_SITE = site_dir
  render_site(site_dir)
  remove_withheld_homework(site_dir)


def remove_withheld_homework(site_dir):
  """Drop the pages and handouts of homework that has not come out yet.

  Runs after render_site, because reading the schedule is what decides which
  those are. Says what it removed: a homework silently vanishing from the site
  is the same class of failure as one silently appearing with its answers.
  """
  homework_dir = site_dir / 'book' / 'homework'
  for stem in WITHHELD_HOMEWORK:
    for target in (homework_dir / f'{stem}.html',
                   homework_dir / f'{stem}_files',
                   homework_dir / 'handouts' / f'{stem}-handout.zip'):
      if not target.exists():
        continue
      if target.is_dir():
        shutil.rmtree(target)
      else:
        target.unlink()
      print(f'withheld (not out yet): {target.relative_to(site_dir)}')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--course-dir', type=Path, required=True)
  parser.add_argument('--book-dir', type=Path)
  parser.add_argument('--site-dir', type=Path, default=Path('_site'))
  args = parser.parse_args()
  COURSE_DIR = args.course_dir.resolve()
  SCHEDULE_SOURCE = COURSE_DIR / 'index.qmd'
  ACTIVE_SITE = args.site_dir
  if args.book_dir:
    assemble_static(args.book_dir, args.site_dir)
  else:
    render_site(args.site_dir)
