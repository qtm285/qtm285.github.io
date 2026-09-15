const COURSE_ID = 'qtm285'

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit',
  }).format(new Date(value))
}

function assignmentHref(assignment) {
  if (!assignment.sourceDocKey) return null
  const outer = new URL(window.top.location.href)
  outer.searchParams.set('project', assignment.sourceDocKey)
  outer.searchParams.set('course', COURSE_ID)
  outer.hash = ''
  return outer.toString()
}

export function classifyAssignment(assignment, now = new Date()) {
  const due = new Date(assignment.dueAt)
  const submission = assignment.submission
  if (!submission && due < now) return { kind: 'late', label: `Late — no submission recorded. Due ${formatDate(due)}.` }
  if (!submission) return { kind: 'open', label: `Due ${formatDate(due)}.` }
  const submitted = new Date(submission.submittedAt)
  if (submitted > due) return { kind: 'submitted-late', label: `Submitted late ${formatDate(submitted)}.` }
  if (submission.gradingStatus === 'returned') return { kind: 'returned', label: 'Returned with feedback.' }
  if (submission.gradingStatus === 'graded') return { kind: 'graded', label: 'Graded; feedback has not been returned yet.' }
  return { kind: 'submitted', label: `Submitted ${formatDate(submitted)}.` }
}

export function chooseUpcoming(assignments, now = new Date()) {
  const rows = assignments.map(assignment => ({ assignment, status: classifyAssignment(assignment, now) }))
  const actionable = rows.filter(row => row.status.kind === 'late' || row.status.kind === 'open')
  const acknowledgedLate = rows.filter(row => row.status.kind === 'submitted-late')
  const next = actionable[0] || acknowledgedLate.at(-1) || rows.at(-1) || null
  const soon = actionable.filter(row => row !== next).slice(0, 3)
  return { next, soon }
}

function assignmentItem(row) {
  const item = document.createElement('li')
  item.className = 'course-now-item'
  const href = assignmentHref(row.assignment)
  const title = href ? document.createElement('a') : document.createElement('strong')
  title.textContent = row.assignment.title
  if (href) {
    title.href = href
    title.target = '_top'
  }
  item.append(title)
  const status = document.createElement('span')
  status.className = `course-now-status${row.status.kind === 'late' ? ' course-now-late' : ''}`
  status.textContent = row.status.label
  item.append(status)
  return item
}

function renderAssignments(root, assignments) {
  const { next, soon } = chooseUpcoming(assignments)
  root.replaceChildren()
  const heading = document.createElement('h2')
  heading.textContent = 'Next up'
  root.append(heading)
  if (!next) {
    const empty = document.createElement('p')
    empty.textContent = 'No assignments are listed yet.'
    root.append(empty)
    return
  }
  const nextList = document.createElement('ul')
  nextList.className = 'course-now-list'
  nextList.append(assignmentItem(next))
  root.append(nextList)
  if (soon.length) {
    const soonHeading = document.createElement('h3')
    soonHeading.textContent = 'Coming soon'
    root.append(soonHeading)
    const soonList = document.createElement('ul')
    soonList.className = 'course-now-list'
    soon.forEach(row => soonList.append(assignmentItem(row)))
    root.append(soonList)
  }
}

function renderNotEnrolled(root) {
  root.replaceChildren()
  const heading = document.createElement('h2')
  heading.textContent = 'Next up'
  const message = document.createElement('p')
  message.textContent = 'This page cannot see an enrolled QTM 285 student on this device. The schedule and course information below are still available.'
  root.append(heading, message)
}

export async function loadCourseIndex(root, fetcher = fetch) {
  const classroomToken = new URLSearchParams(window.location.search).get('classroomToken')
  if (!classroomToken) return renderNotEnrolled(root)
  const url = `/api/classroom/courses/${encodeURIComponent(COURSE_ID)}/assignments?classroomToken=${encodeURIComponent(classroomToken)}`
  const response = await fetcher(url)
  if (response.status === 401 || response.status === 403) return renderNotEnrolled(root)
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  const data = await response.json()
  renderAssignments(root, data.assignments || [])
}

const root = typeof document === 'undefined' ? null : document.querySelector('#course-now')
if (root) loadCourseIndex(root).catch(() => {
  root.querySelector('.course-now-loading').textContent = 'Course status is temporarily unavailable. The schedule and course information below are still available.'
})
