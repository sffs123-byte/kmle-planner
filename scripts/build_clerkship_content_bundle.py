#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

PRIORITY_SCORE_MAP = {
    "최상": 9,
    "상": 7,
    "중": 5,
    "낮음": 3,
    "확인필요": 5,
}
PACKET_DIFFICULTY_MAP = {
    "low": 3,
    "medium": 5,
    "high": 7,
    "very_high": 9,
    "critical": 10,
}
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


def parse_time(raw: str) -> tuple[Optional[str], Optional[str], str]:
    raw = (raw or "").strip()
    matches = re.findall(r"\d{1,2}:\d{2}", raw)
    if len(matches) >= 2:
        return matches[0], matches[1], f"{matches[0]}~{matches[1]}"
    if len(matches) == 1:
        return matches[0], None, matches[0]
    return None, None, raw or "시간 추후확인"


def classify_event_type(kind: Optional[str], title: str) -> str:
    mapping = {
        'orientation': 'admin',
        'prep': 'session',
        'lecture': 'session',
        'interactive_lecture': 'session',
        'teaching': 'session',
        'patient_assignment': 'presentation',
        'skill_feedback': 'exam',
        'rounding': 'session',
        'outpatient': 'session',
        'feedback': 'exam',
        'presentation': 'presentation',
        'discussion': 'presentation',
        'exam': 'exam'
    }
    if kind and kind in mapping:
        return mapping[kind]
    if any(word in title for word in ['예진평가', 'Mini-CEX', '임상추론평가', '피드백']):
        return 'exam'
    if any(word in title for word in ['증례발표', '토의', '케이스']):
        return 'presentation'
    if any(word in title for word in ['오리엔테이션', '환자 배정']):
        return 'admin'
    return 'session'


def packet_diff(label: Optional[str]) -> int:
    return PACKET_DIFFICULTY_MAP.get((label or '').lower(), 5)


class ProfessorRubric:
    def __init__(self, data: Dict[str, Any]) -> None:
        self.professors = data.get('professors', {})

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
            if 'alias_of' in record:
                current = record['alias_of']
                continue
            return record
        return None

    def score(self, name: Optional[str]) -> int:
        rec = self.resolve(name)
        if rec and isinstance(rec.get('score'), int):
            return rec['score']
        return 5


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


def normalize_title(value: str) -> str:
    value = re.sub(r"[-–—]+", " ", value or "")
    return re.sub(r"\s+", " ", value.replace('교수님', '').strip()).lower()


def match_packet_session(packet_sessions: List[Dict[str, Any]], week: str, day: str, title: str, time: str) -> Optional[Dict[str, Any]]:
    title_norm = normalize_title(title)
    time_norm = re.sub(r"\s+", '', time)
    for session in packet_sessions:
        if session.get('week') != week or session.get('day') != day:
            continue
        if normalize_title(session.get('title', '')) != title_norm:
            continue
        pkt_time = re.sub(r"\s+", '', session.get('time', ''))
        if time_norm and pkt_time and time_norm != pkt_time:
            continue
        return session
    return None


def compute_session_difficulty(professor_score: int, event_type: str, packet_session: Optional[Dict[str, Any]]) -> int:
    packet_score = packet_diff(packet_session.get('difficulty')) if packet_session else 5
    value = round((professor_score + packet_score + (5 + EVENT_TYPE_WEIGHT.get(event_type, 0))) / 3)
    return max(1, min(10, value))


def assignment_priority_value(label: Optional[str]) -> int:
    return PRIORITY_SCORE_MAP.get(label or '', 5)


def content_note(intro: List[str], summary: List[str], prepare: List[str]) -> str:
    parts: List[str] = []
    if intro:
        parts.append(intro[0])
    if summary:
        parts.append('핵심: ' + ' / '.join(summary[:2]))
    if prepare:
        parts.append('준비: ' + ' / '.join(prepare[:2]))
    return ' · '.join(parts)


def build_sessions(content: Dict[str, Any], packet: Dict[str, Any], config: Dict[str, Any], rubric: ProfessorRubric, audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    sessions: List[Dict[str, Any]] = []
    packet_sessions = packet.get('sessions', [])
    overrides = config.get('session_overrides', [])
    for week, days in content['weeks'].items():
        for day, block in days.items():
            date = config['week_date_map'][week][day]
            day_summary = block.get('day_summary', [])
            for idx, item in enumerate(block.get('items', []), start=1):
                title = item.get('title', '')
                override = find_override(overrides, week, day, title)
                packet_session = match_packet_session(packet_sessions, week, day, title, item.get('time', ''))
                status = (packet_session or {}).get('status', item.get('status', 'active'))
                if status == 'excluded' or (override and override.get('action') == 'exclude'):
                    audit['excluded_sessions'].append({
                        'week': week,
                        'day': day,
                        'title': title,
                        'reason': 'packet status excluded' if status == 'excluded' else override.get('reason', 'excluded by override')
                    })
                    continue

                session_date = date
                time_raw = item.get('time', '')
                professor = item.get('professor', '') or (packet_session or {}).get('professor', '')
                intro = list(item.get('sections', {}).get('intro', []))
                summary = list(item.get('sections', {}).get('핵심 정리', []))
                prepare = list(item.get('sections', {}).get('준비 / 운영 포인트', []))
                questions = list(item.get('sections', {}).get('질문 / 예시 포인트', []))
                research = list(item.get('sections', {}).get('조사 / 보강 내용', []))
                note_append = None
                if override and override.get('replace'):
                    repl = override['replace']
                    title = repl.get('title', title)
                    if repl.get('title_suffix'):
                        title += repl['title_suffix']
                    session_date = repl.get('date', session_date)
                    time_raw = repl.get('time', time_raw)
                    professor = repl.get('professor', professor)
                    note_append = repl.get('note_append')
                if note_append:
                    research.append(note_append)

                start_time, end_time, time_label = parse_time(time_raw)
                event_type = classify_event_type((packet_session or {}).get('kind'), title)
                professor_score = rubric.score(professor)
                difficulty = compute_session_difficulty(professor_score, event_type, packet_session)
                note = content_note(intro, summary, prepare)
                session_token = f"{session_date}-{week}-{day}-{idx}-{(start_time or 'na').replace(':','')}-{(end_time or 'na').replace(':','')}"
                sessions.append({
                    'id': f"session-{safe_id(session_token)}",
                    'clerkship': config['meta']['clerkship_id'],
                    'week': week,
                    'day': day,
                    'date': session_date,
                    'time_raw': time_raw,
                    'start_time': start_time,
                    'end_time': end_time,
                    'time_label': time_label,
                    'title': title,
                    'title_raw': item.get('title_raw', title),
                    'title_tail': item.get('title_tail', ''),
                    'professor': professor,
                    'professor_score': professor_score,
                    'event_type': event_type,
                    'difficulty': difficulty,
                    'status': status,
                    'kind': (packet_session or {}).get('kind', ''),
                    'start_when': (packet_session or {}).get('start_when', ''),
                    'follow_up': (packet_session or {}).get('follow_up', ''),
                    'needs_confirmation': bool((packet_session or {}).get('needs_confirmation', False)),
                    'day_summary': day_summary,
                    'sections': {
                        'intro': intro,
                        '핵심 정리': summary,
                        '준비 / 운영 포인트': prepare,
                        '질문 / 예시 포인트': questions,
                        '조사 / 보강 내용': research
                    },
                    'summary': intro[0] if intro else '',
                    'note': note
                })
    sessions.sort(key=lambda x: (x['date'], x.get('start_time') or '99:99', x['title']))
    return sessions


def match_session_ids(sessions: List[Dict[str, Any]], keywords: List[str]) -> List[str]:
    if not keywords:
        return []
    normalized_keywords = [normalize_title(k) for k in keywords if k]
    out = []
    for s in sessions:
        haystacks = [
            normalize_title(s.get('title', '')),
            normalize_title(s.get('title_raw', '')),
        ]
        if any(keyword and keyword in hay for keyword in normalized_keywords for hay in haystacks if hay):
            out.append(s['id'])
    return out


def build_assignments(content: Dict[str, Any], packet: Dict[str, Any], config: Dict[str, Any], sessions: List[Dict[str, Any]], audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    packet_map = {task['name']: task for task in packet.get('assignments', [])}
    overrides = config.get('assignment_overrides', {})
    sessions_by_id = {s['id']: s for s in sessions}
    assignments = []
    for idx, task in enumerate(content.get('과제 표', []), start=1):
        name = task['과제']
        packet_task = packet_map.get(name, {})
        override = overrides.get(name, {})
        if not override:
            audit['unconfigured_assignments'].append(name)
        linked_ids = match_session_ids(sessions, override.get('linked_session_keywords', []))
        linked_professors = []
        linked_scores = []
        for sid in linked_ids:
            prof = sessions_by_id[sid].get('professor')
            if prof and prof not in linked_professors:
                linked_professors.append(prof)
                linked_scores.append(sessions_by_id[sid].get('professor_score') or 5)
        content_diff = override.get('difficulty_content') or assignment_priority_value(task.get('우선도'))
        operational_diff = override.get('difficulty_operational') or packet_diff(packet_task.get('difficulty')) or assignment_priority_value(task.get('우선도'))
        professor_score = max(linked_scores) if linked_scores else 5
        total = max(1, min(10, round((content_diff + operational_diff + professor_score) / 3)))
        due_token = re.sub(r'[^0-9]', '', str(override.get('hard_deadline') or task.get('마감') or ''))[:12] or f'{idx:02d}'
        assignments.append({
            'id': f"assignment-{safe_id(config['meta']['track'] + '-' + due_token + '-' + str(idx))}",
            'name': name,
            'priority_label': task.get('우선도'),
            'priority_score': assignment_priority_value(task.get('우선도')),
            'format': task.get('형식'),
            'raw_deadline': task.get('마감'),
            'start_when': packet_task.get('start_when', ''),
            'start_at': override.get('start_at'),
            'soft_deadline': override.get('soft_deadline'),
            'hard_deadline': override.get('hard_deadline'),
            'followup_deadline': override.get('followup_deadline'),
            'follow_up': packet_task.get('follow_up', ''),
            'needs_confirmation': bool(packet_task.get('needs_confirmation', override.get('needs_confirmation', False))),
            'difficulty_content': int(content_diff),
            'difficulty_operational': int(operational_diff),
            'difficulty_total': int(total),
            'linked_session_ids': linked_ids,
            'linked_professors': linked_professors,
            'milestones': override.get('milestones', []),
            'notes': override.get('notes', []),
            'content_summary': f"{task.get('형식')} · 마감: {task.get('마감')}",
            'source_ids': task.get('source_ids', [])
        })
    assignments.sort(key=lambda x: (x.get('hard_deadline') or '9999', -x.get('difficulty_total', 0), x['name']))
    return assignments


def build_daily_briefing_seed(sessions: List[Dict[str, Any]], assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_date: Dict[str, List[Dict[str, Any]]] = {}
    for session in sessions:
        by_date.setdefault(session['date'], []).append(session)
    starts = {}
    dues = {}
    for assignment in assignments:
        if assignment.get('start_at'):
            starts.setdefault(assignment['start_at'][:10], []).append(assignment['name'])
        if assignment.get('hard_deadline'):
            dues.setdefault(assignment['hard_deadline'][:10], []).append(assignment['name'])
    out = []
    for date, items in sorted(by_date.items()):
        items.sort(key=lambda x: x.get('start_time') or '99:99')
        out.append({
            'date': date,
            'headline': items[0]['day_summary'][0] if items and items[0].get('day_summary') else items[0]['title'],
            'day_summary': items[0].get('day_summary', []) if items else [],
            'sessions': [
                {
                    'time': s['time_label'],
                    'title': s['title'],
                    'professor': s.get('professor'),
                    'difficulty': s.get('difficulty'),
                    'intro': s['sections'].get('intro', [])[:2],
                    'prepare_points': s['sections'].get('준비 / 운영 포인트', [])[:3]
                }
                for s in items
            ],
            'assignment_start_today': starts.get(date, []),
            'assignment_due_today': dues.get(date, []),
            'max_professor_score': max((s.get('professor_score') or 5) for s in items),
            'max_session_difficulty': max((s.get('difficulty') or 5) for s in items)
        })
    return out


def build_day_reminders(sessions: List[Dict[str, Any]], assignments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_date: Dict[str, Dict[str, List[str]]] = {}
    for session in sessions:
        payload = by_date.setdefault(session['date'], {'prepare': [], 'watchouts': [], 'sessions': []})
        payload['sessions'].append(session['title'])
        for item in session['sections'].get('준비 / 운영 포인트', [])[:4]:
            if item not in payload['prepare']:
                payload['prepare'].append(item)
        if session.get('needs_confirmation'):
            payload['watchouts'].append(f"확인 필요: {session['title']}")
        for item in session['sections'].get('질문 / 예시 포인트', [])[:2]:
            if item not in payload['watchouts']:
                payload['watchouts'].append(item)
    for assignment in assignments:
        if assignment.get('start_at'):
            date = assignment['start_at'][:10]
            payload = by_date.setdefault(date, {'prepare': [], 'watchouts': [], 'sessions': []})
            payload['prepare'].append(f"과제 착수: {assignment['name']}")
        if assignment.get('hard_deadline'):
            date = assignment['hard_deadline'][:10]
            payload = by_date.setdefault(date, {'prepare': [], 'watchouts': [], 'sessions': []})
            payload['watchouts'].append(f"마감: {assignment['name']}")
    return [
        {
            'date': date,
            'sessions': payload['sessions'],
            'prepare': payload['prepare'][:8],
            'watchouts': payload['watchouts'][:8]
        }
        for date, payload in sorted(by_date.items())
    ]


def session_to_calendar_event(bundle: Dict[str, Any], session: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': f"event-{safe_id(bundle['meta']['clerkship_id'])}-{safe_id(session['id'])}",
        'date': session['date'],
        'type': session['event_type'],
        'title': session['title'],
        'time': session['time_label'],
        'note': session['summary'] or session['note'],
        'completed': False,
        'professor': session.get('professor') or '',
        'difficulty': session.get('difficulty'),
        'track': bundle['meta'].get('track', ''),
        'windowType': 'clerkship-session',
        'bundleId': bundle['meta']['clerkship_id'],
        'sourceSessionId': session['id'],
        'sourceAssignmentId': '',
        'sourceKind': 'session'
    }


def monday_start(date_text: str) -> datetime:
    date = datetime.fromisoformat(date_text)
    return date - timedelta(days=date.weekday())


def assignment_summary_label(assignment: Dict[str, Any]) -> str:
    start_date = (assignment.get('start_at') or '')[:10]
    end_date = (assignment.get('hard_deadline') or '')[:10]
    if start_date and end_date and start_date != end_date:
        return f"{start_date[5:]}~{end_date[5:]}"
    if end_date:
        return end_date[5:]
    if start_date:
        return start_date[5:]
    return '기간 확인'


def assignment_to_events(bundle: Dict[str, Any], assignment: Dict[str, Any]) -> List[Dict[str, Any]]:
    prefix = safe_id(bundle['meta']['clerkship_id'])
    start_date = (assignment.get('start_at') or assignment.get('hard_deadline') or '')[:10]
    end_date = (assignment.get('hard_deadline') or assignment.get('start_at') or '')[:10]
    if not start_date:
        return []

    week_cursor = monday_start(start_date)
    last_week = monday_start(end_date)
    anchors = []
    while week_cursor <= last_week:
        anchor_date = max(week_cursor.date().isoformat(), start_date)
        if anchor_date <= end_date:
            anchors.append(anchor_date)
        week_cursor += timedelta(days=7)

    label = assignment_summary_label(assignment)
    out = []
    for idx, anchor_date in enumerate(anchors, start=1):
        out.append({
            'id': f"event-{prefix}-{safe_id(assignment['id'])}-summary-w{idx}",
            'date': anchor_date,
            'type': 'assignment',
            'title': assignment['name'],
            'time': label,
            'note': assignment.get('content_summary', ''),
            'completed': False,
            'difficulty': assignment.get('difficulty_total'),
            'track': bundle['meta'].get('track', ''),
            'windowType': 'assignment-summary',
            'bundleId': bundle['meta']['clerkship_id'],
            'sourceSessionId': '',
            'sourceAssignmentId': assignment['id'],
            'sourceKind': 'assignment'
        })
    return out


def assignment_to_tasks(bundle: Dict[str, Any], assignment: Dict[str, Any], subject_id: str) -> List[Dict[str, Any]]:
    return []


def normalize_for_app_state(base_state: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(base_state)
    state.setdefault('calendarEvents', [])
    state.setdefault('tasks', [])
    state.setdefault('clerkshipBundles', {})
    state['clerkshipBundles'][bundle['meta']['clerkship_id']] = bundle
    subject = next((s for s in state.get('subjects', []) if s.get('name') == '호흡기'), None)
    subject_id = subject.get('id') if subject else 'subject-canary-resp'
    prefix = f"clerkship-{safe_id(bundle['meta']['clerkship_id'])}"
    state['calendarEvents'] = [e for e in state['calendarEvents'] if not str(e.get('id','')).startswith(prefix)]
    state['tasks'] = [t for t in state['tasks'] if not str(t.get('id','')).startswith(prefix)]
    for session in bundle['sessions']:
        state['calendarEvents'].append(session_to_calendar_event(bundle, session))
    for assignment in bundle['assignments']:
        state['calendarEvents'].extend(assignment_to_events(bundle, assignment))
    state['calendarEvents'].sort(key=lambda x: (x.get('date','9999'), x.get('time','99:99'), x.get('title','')))
    state['tasks'].sort(key=lambda x: (x.get('date','9999'), x.get('startTime','99:99'), x.get('title','')))
    return state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--content', required=True)
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

    content = load_json(Path(args.content))
    packet = load_json(Path(args.packet))
    config = load_json(Path(args.config))
    rubric_data = load_json(Path(args.rubric))
    base_state = load_json(Path(args.base_state))

    audit = {'excluded_sessions': [], 'unconfigured_assignments': [], 'warnings': []}
    rubric = ProfessorRubric(rubric_data)
    sessions = build_sessions(content, packet, config, rubric, audit)
    assignments = build_assignments(content, packet, config, sessions, audit)
    briefings = build_daily_briefing_seed(sessions, assignments)
    reminders = build_day_reminders(sessions, assignments)
    bundle = {
        'meta': {
            'clerkship_id': config['meta']['clerkship_id'],
            'subject': config['meta']['subject'],
            'track': config['meta']['track'],
            'generated_at': datetime.now().isoformat(timespec='seconds'),
            'content_source': content.get('meta', {}),
            'packet_source': packet.get('meta', {}),
            'config_source': config.get('meta', {}),
            'rubric_source': rubric_data.get('meta', {})
        },
        'global_rules': content.get('제출 공통 메모', []),
        'fixed_info': content.get('고정 정보', {}),
        'submission_rules': content.get('과제 표', []),
        'sessions': sessions,
        'assignments': assignments,
        'daily_briefing_seed': briefings,
        'day_reminders': reminders,
        'outpatient_professors': content.get('외래 교수님 추천표', []),
        'analysis_appendix': packet.get('analysis_flags', {}),
        'audit': audit
    }
    planner_state = normalize_for_app_state(base_state, bundle)
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
