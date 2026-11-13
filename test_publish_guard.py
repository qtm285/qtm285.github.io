#!/usr/bin/env python3
"""Unit and counterfactual tests for publish_guard.schedule_violations."""
from pathlib import Path
import unittest

from publish_guard import schedule_violations_html


CLEAN_LANDING = '''
<div class="row" id="schedule">
<h5> Part 1: One-Sample Inference </h5>
<table><tbody>
<tr><td>Th&nbsp;Aug&nbsp;27,&nbsp;4:00</td><td> Intro </td></tr>
<tr><td>Th&nbsp;Aug&nbsp;27,&nbsp;11:59</td><td> <a href="book/homework/homework-setup.html">HW −1</a> out &middot; <a href="book/homework/homework-descriptive.html">HW 0</a> out </td></tr>
<tr><td>Th&nbsp;Sep&nbsp;3,&nbsp;4:00</td><td> Estimates </td></tr>
<tr><td>Th&nbsp;Sep&nbsp;3,&nbsp;11:59</td><td> HW 0 due </td></tr>
</tbody></table>
<p><b>About the Midterm</b></p>
<h5> Part 2: Two-Sample Problems, Randomization, and Models </h5>
<table><tbody>
<tr><td>Th&nbsp;Nov&nbsp;5,&nbsp;4:00</td><td> Randomization </td></tr>
<tr><td>Th&nbsp;Nov&nbsp;5,&nbsp;11:59</td><td> <a href="book/homework/homework-06.html">HW 6</a> out </td></tr>
<tr><td>Th&nbsp;Nov&nbsp;12,&nbsp;4:00</td><td> Sampling </td></tr>
<tr><td>Th&nbsp;Nov&nbsp;12,&nbsp;11:59</td><td> HW 6 due </td></tr>
</tbody></table>
</div>
<div class="row" id="practices"></div>
'''

CLEAN_BOOK = '''
<section id="schedule" class="level2">
<section id="part-1-one-sample-inference" class="level3">
<h3>Part 1: One-Sample Inference</h3>
<table class="caption-top table"><tbody><tr><td>Th Aug 27</td><td>Intro</td></tr></tbody></table>
<p><strong>About the Midterm</strong></p>
</section>
<section id="part-2-two-sample-problems-randomization-and-models" class="level3">
<h3>Part 2: Two-Sample Problems, Randomization, and Models</h3>
<table class="caption-top table"><tbody><tr><td>Th Nov 5</td><td>Randomization</td></tr></tbody></table>
</section>
</section>
<section id="class-practices" class="level2"></section>
'''


class PublishGuardScheduleTest(unittest.TestCase):
    def test_clean_schedule_passes(self):
        self.assertEqual(schedule_violations_html(CLEAN_LANDING, CLEAN_BOOK), [])

    def test_split_part_table_and_prose_hw_note_fail(self):
        sabotaged = CLEAN_LANDING.replace(
            '<tr><td>Th&nbsp;Nov&nbsp;5,&nbsp;11:59</td><td> <a href="book/homework/homework-06.html">HW 6</a> out </td></tr>\n',
            '</tbody></table>\n<p><em><a href="book/homework/homework-06.html">HW 6</a> was posted on Sunday, November 8.</em></p>\n<table><tbody>\n',
        ).replace(
            '<tr><td>Th&nbsp;Nov&nbsp;12,&nbsp;11:59</td><td> HW 6 due </td></tr>\n',
            '',
        )
        issues = schedule_violations_html(sabotaged, CLEAN_BOOK)
        self.assertTrue(any('has 2 <table>' in i for i in issues), issues)
        self.assertTrue(any('prose paragraph' in i for i in issues), issues)

    def test_missing_hw_due_row_fails(self):
        no_due = CLEAN_LANDING.replace(
            '<tr><td>Th&nbsp;Nov&nbsp;12,&nbsp;11:59</td><td> HW 6 due </td></tr>\n',
            '',
        )
        issues = schedule_violations_html(no_due, CLEAN_BOOK)
        self.assertTrue(any('HW 6 due' in i for i in issues), issues)

    def test_unlinked_solutions_backslash_em_and_book_ul_fail(self):
        bad_landing = CLEAN_LANDING.replace(
            '<tr><td>Th&nbsp;Sep&nbsp;3,&nbsp;11:59</td><td> HW 0 due </td></tr>',
            '<tr><td>Th&nbsp;Sep&nbsp;3,&nbsp;11:59</td><td> HW 0 due [solutions] &middot; Foo\\<em>\\</em> </td></tr>',
        )
        bad_book = CLEAN_BOOK.replace(
            '<h3>Part 1: One-Sample Inference</h3>',
            '<h3>Part 1: One-Sample Inference</h3><ul><li>A starred chapter</li></ul>',
        )
        issues = schedule_violations_html(bad_landing, bad_book)
        self.assertTrue(any('unlinked "[solutions]"' in i for i in issues), issues)
        self.assertTrue(any('backslash-asterisk' in i for i in issues), issues)
        self.assertTrue(any('unintended <ul>' in i for i in issues), issues)


if __name__ == '__main__':
    unittest.main()
