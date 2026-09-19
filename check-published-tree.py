#!/usr/bin/env python3
"""Refuse to publish a tree that serves worked solutions.

Run by `.github/workflows/pages.yml` against the committed tree, before the
upload step. This is the boundary: the workflow uploads `path: .`, so whatever
is committed is what students get, however it got there. `build-site.py` is one
way to write that tree and the record shows it is not the usual one.

Exit 1 fails the deploy. Nothing is published.

To publish a page that carries solutions anyway, add its path to
`publish-allow-solutions.txt` and commit that. The override is a line in a diff
with the page's name in it.
"""

import argparse
import sys
from pathlib import Path

from publish_guard import solution_violations

DEFAULT_ALLOWLIST = 'publish-allow-solutions.txt'


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('--site-dir', type=Path, default=Path('static'))
  parser.add_argument('--allowlist', type=Path, default=Path(DEFAULT_ALLOWLIST))
  args = parser.parse_args()

  if not args.site_dir.is_dir():
    print(f'{args.site_dir} is not a directory, so there is no published tree to check',
          file=sys.stderr)
    return 1

  violations = solution_violations(args.site_dir, args.allowlist)
  if not violations:
    print(f'{args.site_dir}: no published chapter carries worked solutions')
    return 0

  total = sum(row['blocks'] for row in violations)
  print(f'{len(violations)} published chapter(s) carry {total} worked solution(s), '
        f'which this site must not serve:', file=sys.stderr)
  for row in violations:
    print(f'  {row["page"]}  — {row["blocks"]} solution callout(s)', file=sys.stderr)
  print(f'\nNothing was published. Either re-render the chapter with '
        f'`withhold-solutions: true` in its source, or, to serve it anyway, add its '
        f'path to {args.allowlist} and commit that.', file=sys.stderr)
  return 1


if __name__ == '__main__':
  sys.exit(main())
