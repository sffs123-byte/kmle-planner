#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PRIORITY_SCORE_MAP = {
    "최상": 9,
    "상": 7,
    "중": 5,
    "낮음": 3,
    "확인필요": 5,
}

EVENT_TYPE_DEFAULT = "assignment"
EVENT_TYPE_WEIGHT = {
    "admin": -2,
    "assignment": -1,
    "presentation": 1,
    "exam": 2,
    "chief": 2,
}


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def safe_id(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


class ProfessorRubric:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.professors = data.get("professors", {})

    def resolve(self, name: Optional[str]) -> Optional[Dict[str, Any]]:
        if not name:
            return None
        current = name
        visited = set()
        while current and current not in visited:
            visited.add(current)
            record = self.professors.get(current)
            if not record:
                return None
            if "alias_of" in record:
                current = record["alias_of"]
                continue
            return record
        return None

    def score(self, name: Optional[str]) -> int:
        rec = self.resolve(name)
        if rec and isinstance(rec.get("score"), int):
            return rec["score"]
        return 5


def parse_time(raw: str) -> tuple[Optional[str], Optional[str], str]:
    raw = (raw or "").strip()
    matches = re.findall(r"\d{1,2}:\d{2}", raw)
    if len(matches) >= 2:
        return matches[0], matches[1], f"{matches[0]}~{matches[1]}"
    if len(matches) == 1:
        return matches[0], None, matches[0]
    return None, None, raw or "시간 추후확인"


def classify_event_type(title: str) -> str:
    rules = [
        (['오리엔테이션', '환자 배정'], 'admin'),
        (['예진평가', 'Mini-CEX', 'mini CEX', '임상추론평가', '피드백'], 'exam'),
        (['증례발표', '케이스', '토의'], 'presentation'),
        (['조장'], 'chief'),
    ]
    for needles, result in rules:
        if any(n in title for n in needles):
            return result
    return EVENT_TYPE_DEFAULT


def classify_event_type_from_kind(kind: Optional[str], title: str) -> str:
    mapping = {
        'orientation': 'admin',
        'prep': 'assignment',
        'lecture': 'assignment',
        'interactive_lecture': 'assignment',
        'teaching': 'assignment',
        'patient_assignment': 'presentation',
        'skill_feedback': 'exam',
        'rounding': 'assignment',
        'outpatient': 'assignment',
        'feedback': 'exam',
        'presentation': 'presentation',
        'discussion': 'presentation',
        'exam': 'exam'
    }
    if kind and kind in mapping:
        return mapping[kind]
    return classify_event_type(title)


def priority_value(label: Optional[str]) -> int:
    return PRIORITY_SCORE_MAP.get(label or '', 5)


def packet_difficulty_value(label: Optional[str]) -> int:
    mapping = {
        'low': 3,
        'medium': 5,
        'high': 7,
        'very_high': 9,
        'critical': 10
    }
    return mapping.get((label or '').lower(), 5)


def compute_session_difficulty(professor_score: int, event_type: str) -> int:
    return max(1, min(10, professor_score + EVENT_TYPE_WEIGHT.get(event_type, 0)))


def make_note(item: Dict[str, Any]) -> str:
    chunks: List[str] = []
    if item.get('summary'):
        chunks.append(item['summary'])
    elif item.get('note'):
        chunks.append(item['note'])
    if item.get('focus_points'):
        chunks.append('핵심: ' + ' / '.join(item['focus_points'][:2]))
    if item.get('prepare_points'):
        chunks.append('준비: ' + ' / '.join(item['prepare_points'][:2]))
    return ' · '.join([c for c in chunks if c])


def find_override(overrides: List[Dict[str, Any]], week: str, day: str, title: str) -> Optional[Dict[str, Any]]:
    for override in overrides:
        match = override.get('match', {})
        if match.get('week') and match['week'] != week:
            continue
        if match.get('day') and match['day'] != day:
            continue
        if match.get('title_contains') and match['title_contains'] not in title:
            continue
        return override
    return None


def normalize_sessions(packet: Dict[str, Any], config: Dict[str, Any], rubric: ProfessorRubric, audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    sessions: List[Dict[str, Any]] = []
    overrides = config.get('session_overrides', [])
    if 'weeks' in packet:
        source_iter = []
        for week, days in packet['weeks'].items():
            for day, block in days.items():
                for idx, item in enumerate(block.get('items', []), start=1):
                    source_iter.append((week, day, config['week_date_map'][week][day], idx, item, block.get('day_digest', [])))
    else:
        source_iter = []
        for idx, item in enumerate(packet.get('sessions', []), start=1):
            week = item['week']
            day = item['day']
            source_iter.append((week, day, config['week_date_map'][week][day], idx, item, []))

    for week, day, date, idx, item, day_digest in source_iter:
        title = item.get('title', '')
        override = find_override(overrides, week, day, title)
        if item.get('status') == 'excluded' or (override and override.get('action') == 'exclude'):
            audit['excluded_sessions'].append({
                'week': week,
                'day': day,
                'title': title,
                'reason': 'packet status excluded' if item.get('status') == 'excluded' else override.get('reason', 'excluded by override')
            })
            continue

        session_date = date
        time_raw = item.get('time', '')
        professor = item.get('professor') or None
        note_extra = None
        if override and override.get('replace'):
            repl = override['replace']
            title = repl.get('title', title)
            if repl.get('title_suffix'):
                title += repl['title_suffix']
            session_date = repl.get('date', session_date)
            time_raw = repl.get('time', time_raw)
            professor = repl.get('professor', professor)
            note_extra = repl.get('note_append')

        start_time, end_time, time_label = parse_time(time_raw)
        professor_score = rubric.score(professor)
        event_type = classify_event_type_from_kind(item.get('kind'), title)
        summary = item.get('summary') or item.get('note', '')
        if note_extra:
            summary = (summary + ' · ' + note_extra).strip(' ·')
        sessions.append({
            'id': f"session-{safe_id(week + '-' + day + '-' + str(idx) + '-' + title)}",
            'clerkship': config['meta']['clerkship_id'],
            'week': week,
            'day': day,
            'date': session_date,
            'time_raw': time_raw,
            'start_time': start_time,
            'end_time': end_time,
            'time_label': time_label,
            'title': title,
            'professor': professor,
            'professor_score': professor_score,
            'event_type': event_type,
            'difficulty': compute_session_difficulty(professor_score, event_type),
            'summary': summary,
            'user_points': item.get('user_points', []),
            'focus_points': item.get('focus_points', []),
            'prepare_points': item.get('prepare_points', []),
            'research_notes': item.get('research_notes', []),
            'status': item.get('status', 'active'),
            'day_digest': day_digest,
            'kind': item.get('kind', ''),
            'start_when': item.get('start_when', ''),
            'follow_up': item.get('follow_up', ''),
            'needs_confirmation': bool(item.get('needs_confirmation', False)),
            'note': make_note({**item, 'summary': summary})
        })
    sessions.sort(key=lambda x: (x['date'], x.get('start_time') or '99:99', x['title']))
    return sessions


def match_session_ids(sessions: List[Dict[str, Any]], keywords: List[str]) -> List[str]:
    if not keywords:
        return []
    out = []
    for s in sessions:
        hay = ' '.join([s.get('title',''), s.get('professor') or '', s.get('summary') or ''])
        if any(k in hay for k in keywords):
            out.append(s['id'])
    return out


def build_assignments(packet: Dict[str, Any], config: Dict[str, Any], sessions: List[Dict[str, Any]], audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    overrides = config.get('assignment_overrides', {})
    sessions_by_id = {s['id']: s for s in sessions}
    assignments = []
    task_rows = packet.get('task_rows')
    if task_rows is None:
        task_rows = [
            {
                '과제': task.get('name'),
                '마감': task.get('due'),
                '형식': task.get('format'),
                '우선도': task.get('priority'),
                'source_ids': []
            }
            for task in packet.get('assignments', [])
        ]

    packet_assignments = {task.get('name'): task for task in packet.get('assignments', [])}

    for task in task_rows:
        name = task['과제']
        override = overrides.get(name)
        if not override:
            audit['unconfigured_assignments'].append(name)
            override = {
                'start_at': None,
                'soft_deadline': None,
                'hard_deadline': None,
                'difficulty_content': priority_value(task.get('우선도')),
                'difficulty_operational': priority_value(task.get('우선도')),
                'needs_confirmation': True,
                'notes': ['override 미설정']
            }
        linked_ids = match_session_ids(sessions, override.get('linked_session_keywords', []))
        linked_professors = []
        linked_scores = []
        for sid in linked_ids:
            prof = sessions_by_id[sid].get('professor')
            if prof and prof not in linked_professors:
                linked_professors.append(prof)
                linked_scores.append(sessions_by_id[sid].get('professor_score') or 5)
        packet_task = packet_assignments.get(name, {})
        content = int(override.get('difficulty_content', packet_difficulty_value(packet_task.get('difficulty')) or priority_value(task.get('우선도'))))
        operational = int(override.get('difficulty_operational', packet_difficulty_value(packet_task.get('difficulty')) or priority_value(task.get('우선도'))))
        profscore = max(linked_scores) if linked_scores else 5
        total = max(1, min(10, round((content + operational + profscore) / 3)))
        assignments.append({
            'id': f"assignment-{safe_id(name)}",
            'name': name,
            'priority_label': task.get('우선도'),
            'priority_score': PRIORITY_SCORE_MAP.get(task.get('우선도'), 5),
            'format': task.get('형식'),
            'raw_deadline': task.get('마감'),
            'start_at': override.get('start_at'),
            'soft_deadline': override.get('soft_deadline'),
            'hard_deadline': override.get('hard_deadline'),
            'followup_deadline': override.get('followup_deadline'),
            'needs_confirmation': bool(override.get('needs_confirmation', packet_task.get('needs_confirmation', False))),
            'difficulty_content': content,
            'difficulty_operational': operational,
            'difficulty_total': total,
            'linked_session_ids': linked_ids,
            'linked_professors': linked_professors,
            'milestones': override.get('milestones', []),
            'notes': override.get('notes', []) + ([f"packet start_when: {packet_task.get('start_when')}"] if packet_task.get('start_when') else []),
            'source_ids': task.get('source_ids', [])
        })
    assignments.sort(key=lambda x: (x.get('hard_deadline') or '9999', -x.get('difficulty_total', 0), x['name']))
    return assignments


def build_daily_briefings(packet: Dict[str, Any], sessions: List[Dict[str, Any]], assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    assignments_by_start = {}
    assignments_by_deadline = {}
    for a in assignments:
        if a.get('start_at'):
            assignments_by_start.setdefault(a['start_at'][:10], []).append(a)
        if a.get('hard_deadline'):
            assignments_by_deadline.setdefault(a['hard_deadline'][:10], []).append(a)
    by_date = {}
    for s in sessions:
        by_date.setdefault(s['date'], []).append(s)
    for date, items in sorted(by_date.items()):
        items.sort(key=lambda x: x.get('start_time') or '99:99')
        day_digest = items[0].get('day_digest', []) if items else []
        out.append({
            'date': date,
            'headline': day_digest[0] if day_digest else (items[0]['title'] if items else ''),
            'day_digest': day_digest,
            'sessions': [
                {
                    'time': s['time_label'],
                    'title': s['title'],
                    'professor': s.get('professor'),
                    'difficulty': s.get('difficulty'),
                    'prepare_points': s.get('prepare_points', [])[:3],
                    'focus_points': s.get('focus_points', [])[:3]
                }
                for s in items
            ],
            'assignment_start_today': [a['name'] for a in assignments_by_start.get(date, [])],
            'assignment_due_today': [a['name'] for a in assignments_by_deadline.get(date, [])],
            'max_professor_score': max((s.get('professor_score') or 5) for s in items) if items else 5,
            'max_session_difficulty': max((s.get('difficulty') or 5) for s in items) if items else 5
        })
    return out


def build_day_reminders(sessions: List[Dict[str, Any]], assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_date = {}
    for s in sessions:
        by_date.setdefault(s['date'], {'prepare': [], 'watch': [], 'sessions': []})
        by_date[s['date']]['sessions'].append(s['title'])
        for p in s.get('prepare_points', [])[:3]:
            if p not in by_date[s['date']]['prepare']:
                by_date[s['date']]['prepare'].append(p)
        for p in s.get('focus_points', [])[:3]:
            if p not in by_date[s['date']]['watch']:
                by_date[s['date']]['watch'].append(p)
    for a in assignments:
        if a.get('start_at'):
            date = a['start_at'][:10]
            by_date.setdefault(date, {'prepare': [], 'watch': [], 'sessions': []})
            by_date[date]['prepare'].append(f"과제 착수: {a['name']}")
        if a.get('hard_deadline'):
            date = a['hard_deadline'][:10]
            by_date.setdefault(date, {'prepare': [], 'watch': [], 'sessions': []})
            by_date[date]['watch'].append(f"마감: {a['name']}")
    out = []
    for date, payload in sorted(by_date.items()):
        out.append({
            'date': date,
            'sessions': payload['sessions'],
            'prepare': payload['prepare'][:8],
            'watchouts': payload['watch'][:8]
        })
    return out


def session_to_calendar_event(session: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': f"event-{session['id']}",
        'date': session['date'],
        'type': session['event_type'],
        'title': session['title'],
        'time': session['time_label'],
        'note': session.get('note', ''),
        'completed': False,
        'professor': session.get('professor') or '',
        'difficulty': session.get('difficulty'),
        'track': 'B',
        'windowType': 'clerkship-session'
    }


def assignment_to_calendar_events(assignment: Dict[str, Any]) -> List[Dict[str, Any]]:
    events = []
    if assignment.get('start_at'):
        date, time = assignment['start_at'].split('T', 1)
        events.append({
            'id': f"event-{safe_id(assignment['id'] + '-start')}",
            'date': date,
            'type': 'assignment',
            'title': f"{assignment['name']} 착수",
            'time': time[:5],
            'note': f"운영 {assignment['difficulty_operational']}/10 · 내용 {assignment['difficulty_content']}/10",
            'completed': False,
            'difficulty': assignment['difficulty_total'],
            'track': 'B',
            'windowType': 'assignment-start'
        })
    if assignment.get('hard_deadline'):
        date, time = assignment['hard_deadline'].split('T', 1)
        events.append({
            'id': f"event-{safe_id(assignment['id'] + '-deadline')}",
            'date': date,
            'type': 'exam' if assignment['difficulty_total'] >= 8 else 'assignment',
            'title': f"{assignment['name']} 마감",
            'time': time[:5],
            'note': assignment.get('format') or assignment.get('raw_deadline') or '',
            'completed': False,
            'difficulty': assignment['difficulty_total'],
            'track': 'B',
            'windowType': 'assignment-deadline'
        })
    return events


def assignment_to_task_seed(assignment: Dict[str, Any], subject_id: str) -> List[Dict[str, Any]]:
    tasks = []
    if assignment.get('start_at'):
        date, time = assignment['start_at'].split('T', 1)
        tasks.append({
            'id': f"task-{safe_id(assignment['id'] + '-start')}",
            'date': date,
            'startTime': time[:5],
            'duration': 45,
            'subjectId': subject_id,
            'stageId': 'framework',
            'title': f"{assignment['name']} 시작",
            'memo': f"운영 {assignment['difficulty_operational']}/10 · {assignment['format']}",
            'completed': False,
            'createdAt': datetime.now().isoformat()
        })
    for idx, milestone in enumerate(assignment.get('milestones', []), start=1):
        date, time = milestone['due'].split('T', 1)
        tasks.append({
            'id': f"task-{safe_id(assignment['id'] + '-milestone-' + str(idx))}",
            'date': date,
            'startTime': time[:5],
            'duration': 40,
            'subjectId': subject_id,
            'stageId': 'revise',
            'title': milestone['title'],
            'memo': assignment['name'],
            'completed': False,
            'createdAt': datetime.now().isoformat()
        })
    return tasks


def apply_to_planner(base_state: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(base_state)
    state.setdefault('calendarEvents', [])
    state.setdefault('tasks', [])
    state.setdefault('clerkshipBundles', {})
    state['clerkshipBundles'][bundle['meta']['clerkship_id']] = bundle
    respiratory = next((s for s in state.get('subjects', []) if s.get('name') == '호흡기'), None)
    subject_id = respiratory.get('id') if respiratory else 'subject-canary-resp'
    existing_event_ids = {e.get('id') for e in state['calendarEvents']}
    for s in bundle['sessions']:
        event = session_to_calendar_event(s)
        if event['id'] not in existing_event_ids:
            state['calendarEvents'].append(event)
            existing_event_ids.add(event['id'])
    for a in bundle['assignments']:
        for event in assignment_to_calendar_events(a):
            if event['id'] not in existing_event_ids:
                state['calendarEvents'].append(event)
                existing_event_ids.add(event['id'])
    existing_task_ids = {t.get('id') for t in state['tasks']}
    for a in bundle['assignments']:
        for task in assignment_to_task_seed(a, subject_id):
            if task['id'] not in existing_task_ids:
                state['tasks'].append(task)
                existing_task_ids.add(task['id'])
    state['calendarEvents'].sort(key=lambda x: (x.get('date','9999'), x.get('time','99:99'), x.get('title','')))
    state['tasks'].sort(key=lambda x: (x.get('date','9999'), x.get('startTime','99:99'), x.get('title','')))
    return state


def build_bundle(packet: Dict[str, Any], config: Dict[str, Any], rubric_data: Dict[str, Any]):
    audit = {'excluded_sessions': [], 'unconfigured_assignments': [], 'warnings': []}
    rubric = ProfessorRubric(rubric_data)
    sessions = normalize_sessions(packet, config, rubric, audit)
    assignments = build_assignments(packet, config, sessions, audit)
    briefings = build_daily_briefings(packet, sessions, assignments)
    reminders = build_day_reminders(sessions, assignments)
    bundle = {
        'meta': {
            'clerkship_id': config['meta']['clerkship_id'],
            'subject': config['meta']['subject'],
            'track': config['meta']['track'],
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'packet_source': packet.get('meta', {}),
            'config_source': config.get('meta', {}),
            'rubric_source': rubric_data.get('meta', {})
        },
        'global_rules': packet.get('global_rules', {}),
        'fixed_info': packet.get('fixed_info', {}),
        'submission_rules': packet.get('submission_rules', []),
        'sessions': sessions,
        'assignments': assignments,
        'daily_briefing_seed': briefings,
        'day_reminders': reminders,
        'outpatient_professors': packet.get('outpatient_professors', []),
        'analysis_appendix': packet.get('analysis_appendix', {}),
        'audit': audit
    }
    return bundle, briefings, reminders, audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--config', required=True)
    parser.add_argument('--rubric', required=True)
    parser.add_argument('--base-state', required=True)
    parser.add_argument('--bundle-out', required=True)
    parser.add_argument('--briefing-out', required=True)
    parser.add_argument('--reminders-out', required=True)
    parser.add_argument('--planner-out', required=True)
    parser.add_argument('--audit-out', required=True)
    args = parser.parse_args()

    packet = load_json(Path(args.packet))
    config = load_json(Path(args.config))
    rubric = load_json(Path(args.rubric))
    base_state = load_json(Path(args.base_state))

    bundle, briefings, reminders, audit = build_bundle(packet, config, rubric)
    planner_state = apply_to_planner(base_state, bundle)

    write_json(Path(args.bundle_out), bundle)
    write_json(Path(args.briefing_out), {'meta': bundle['meta'], 'days': briefings})
    write_json(Path(args.reminders_out), {'meta': bundle['meta'], 'days': reminders})
    write_json(Path(args.planner_out), planner_state)
    write_json(Path(args.audit_out), audit)

    print('bundle:', args.bundle_out)
    print('briefing:', args.briefing_out)
    print('reminders:', args.reminders_out)
    print('planner:', args.planner_out)
    print('audit:', args.audit_out)


if __name__ == '__main__':
    main()
