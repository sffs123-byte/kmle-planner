#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


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

STAGE_BY_EVENT_TYPE = {
    "admin": "lecture",
    "assignment": "lecture",
    "presentation": "revise",
    "exam": "review",
    "chief": "framework",
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

    def resolve(self, name: Optional[str]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        if not name:
            return None, None
        visited = set()
        current = name
        while current and current in self.professors and current not in visited:
            visited.add(current)
            record = self.professors[current]
            if "alias_of" in record:
                current = record["alias_of"]
                continue
            return current, record
        return name, self.professors.get(name)

    def score(self, name: Optional[str]) -> int:
        canonical, record = self.resolve(name)
        if record and isinstance(record.get("score"), int):
            return record["score"]
        return 5


def extract_professor(title: str, raw_notes: List[str], rubric: ProfessorRubric) -> Optional[str]:
    title_candidates = []
    for key, record in rubric.professors.items():
        if "alias_of" in record:
            continue
        if key in title:
            title_candidates.append(key)
    if not title_candidates:
        return None
    title_candidates.sort(key=len, reverse=True)
    return title_candidates[0]


def parse_time_strings(raw: str) -> Tuple[Optional[str], Optional[str], str]:
    raw = (raw or "").strip()
    matches = re.findall(r"\d{1,2}:\d{2}", raw)
    if len(matches) >= 2:
        return matches[0], matches[1], f"{matches[0]}~{matches[1]}"
    if len(matches) == 1:
        return matches[0], None, matches[0]
    return None, None, raw or "시간 추후확인"


def classify_event_type(title: str, rules: List[Dict[str, Any]]) -> str:
    for rule in rules:
        for needle in rule.get("contains", []):
            if needle in title:
                return rule["type"]
    return EVENT_TYPE_DEFAULT


def compute_session_difficulty(professor_score: int, event_type: str) -> int:
    value = professor_score + EVENT_TYPE_WEIGHT.get(event_type, 0)
    return max(1, min(10, value))


def find_override(overrides: List[Dict[str, Any]], week: str, day: str, title: str) -> Optional[Dict[str, Any]]:
    for override in overrides:
        match = override.get("match", {})
        if match.get("week") and match["week"] != week:
            continue
        if match.get("day") and match["day"] != day:
            continue
        if match.get("title_contains") and match["title_contains"] not in title:
            continue
        return override
    return None


def session_type_label(event_type: str) -> str:
    return {
        "admin": "운영",
        "assignment": "수업/실습",
        "presentation": "발표",
        "exam": "평가/피드백",
        "chief": "조장"
    }.get(event_type, "일정")


def normalize_sessions(raw: Dict[str, Any], config: Dict[str, Any], rubric: ProfessorRubric, audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    sessions: List[Dict[str, Any]] = []
    schedule = raw.get("schedule", {})
    week_map = config["week_date_map"]
    overrides = config.get("session_overrides", [])
    rules = config.get("event_type_rules", [])

    for week, days in schedule.items():
        for day, entries in days.items():
            date = week_map[week][day]
            for idx, entry in enumerate(entries, start=1):
                title = entry.get("title", "").strip()
                raw_notes = [str(note).strip() for note in entry.get("raw_notes", []) if str(note).strip()]
                override = find_override(overrides, week, day, title)
                if override and override.get("action") == "exclude":
                    audit["excluded_sessions"].append({
                        "week": week,
                        "day": day,
                        "title": title,
                        "reason": override.get("reason", "excluded by override")
                    })
                    continue

                session_date = date
                time_raw = entry.get("time", "")
                note_suffix = None
                if override and override.get("replace"):
                    repl = override["replace"]
                    title = repl.get("title", title)
                    if repl.get("title_suffix"):
                        title += repl["title_suffix"]
                    session_date = repl.get("date", session_date)
                    time_raw = repl.get("time", time_raw)
                    note_suffix = repl.get("note_append")
                if note_suffix:
                    raw_notes = raw_notes + [note_suffix]

                start_time, end_time, time_label = parse_time_strings(time_raw)
                professor = extract_professor(title, raw_notes, rubric)
                if override and override.get("replace", {}).get("professor"):
                    professor = override["replace"]["professor"]
                professor_score = rubric.score(professor)
                event_type = classify_event_type(title, rules)
                session_id = safe_id(f"{week}-{day}-{idx}-{title}")
                session = {
                    "id": f"session-{session_id}",
                    "clerkship": config["meta"]["clerkship_id"],
                    "week": week,
                    "day": day,
                    "date": session_date,
                    "time_raw": time_raw,
                    "start_time": start_time,
                    "end_time": end_time,
                    "time_label": time_label,
                    "slot": entry.get("raw_slot") or None,
                    "title": title,
                    "professor": professor,
                    "professor_score": professor_score,
                    "event_type": event_type,
                    "event_type_label": session_type_label(event_type),
                    "difficulty": compute_session_difficulty(professor_score, event_type),
                    "raw_notes": raw_notes,
                    "source_ids": entry.get("source_ids", []),
                    "summary": entry.get("curated_v7") or entry.get("curated_v8") or entry.get("curated_v9") or entry.get("curated_v10") or entry.get("curated_v11") or None
                }
                sessions.append(session)

    sessions.sort(key=lambda x: (x["date"], x.get("start_time") or "99:99", x["title"]))
    return sessions


def match_session_ids(sessions: List[Dict[str, Any]], keywords: List[str]) -> List[str]:
    if not keywords:
        return []
    matched = []
    for session in sessions:
        haystack = " ".join([session["title"], session.get("professor") or "", session.get("event_type_label") or ""]) 
        if any(keyword in haystack for keyword in keywords):
            matched.append(session["id"])
    return matched


def build_assignment(task: Dict[str, Any], override: Dict[str, Any], sessions_by_id: Dict[str, Dict[str, Any]], sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    name = task["과제"]
    keywords = override.get("linked_session_keywords", [])
    linked_session_ids = match_session_ids(sessions, keywords)
    linked_professors = []
    linked_scores = []
    for session_id in linked_session_ids:
        session = sessions_by_id[session_id]
        if session.get("professor") and session["professor"] not in linked_professors:
            linked_professors.append(session["professor"])
            linked_scores.append(session.get("professor_score") or 5)
    content_difficulty = int(override.get("difficulty_content", PRIORITY_SCORE_MAP.get(task.get("우선도"), 5)))
    operational_difficulty = int(override.get("difficulty_operational", PRIORITY_SCORE_MAP.get(task.get("우선도"), 5)))
    professor_score = max(linked_scores) if linked_scores else 5
    total_difficulty = max(1, min(10, round((content_difficulty + operational_difficulty + professor_score) / 3)))
    return {
        "id": f"assignment-{safe_id(name)}",
        "name": name,
        "priority_label": task.get("우선도"),
        "priority_score": PRIORITY_SCORE_MAP.get(task.get("우선도"), 5),
        "format": task.get("형식"),
        "raw_deadline": task.get("마감"),
        "start_at": override.get("start_at"),
        "soft_deadline": override.get("soft_deadline"),
        "hard_deadline": override.get("hard_deadline"),
        "followup_deadline": override.get("followup_deadline"),
        "needs_confirmation": bool(override.get("needs_confirmation", False)),
        "difficulty_content": content_difficulty,
        "difficulty_operational": operational_difficulty,
        "difficulty_total": total_difficulty,
        "linked_session_ids": linked_session_ids,
        "linked_professors": linked_professors,
        "milestones": override.get("milestones", []),
        "notes": override.get("notes", []),
        "source_ids": task.get("source_ids", [])
    }


def build_assignments(raw: Dict[str, Any], config: Dict[str, Any], sessions: List[Dict[str, Any]], audit: Dict[str, Any]) -> List[Dict[str, Any]]:
    overrides = config.get("assignment_overrides", {})
    sessions_by_id = {session["id"]: session for session in sessions}
    assignments: List[Dict[str, Any]] = []
    for task in raw.get("task_rows", []):
        name = task["과제"]
        override = overrides.get(name)
        if not override:
            audit["unconfigured_assignments"].append(name)
            override = {
                "start_at": None,
                "soft_deadline": None,
                "hard_deadline": None,
                "difficulty_content": PRIORITY_SCORE_MAP.get(task.get("우선도"), 5),
                "difficulty_operational": PRIORITY_SCORE_MAP.get(task.get("우선도"), 5),
                "needs_confirmation": True,
                "notes": ["override 미설정 - 수동 보강 필요"]
            }
        assignments.append(build_assignment(task, override, sessions_by_id, sessions))
    assignments.sort(key=lambda x: (x.get("hard_deadline") or "9999", -x.get("difficulty_total", 0), x["name"]))
    return assignments


def build_daily_windows(sessions: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    by_date: Dict[str, List[Dict[str, Any]]] = {}
    for session in sessions:
        by_date.setdefault(session["date"], []).append(session)
    windows = []
    for date, items in sorted(by_date.items()):
        items.sort(key=lambda x: x.get("start_time") or "99:99")
        high_load = max((item.get("difficulty", 5) for item in items), default=5) >= 8
        has_evening = any((item.get("end_time") or "") >= "17:30" for item in items)
        if high_load and has_evening:
            note = "실습 강도 높음 - 저녁은 짧은 정리 위주"
            level = "low"
        elif high_load:
            note = "실습 피로도 높아 깊은 신규 진도보다 유지 복습 우선"
            level = "medium"
        elif has_evening:
            note = "실습이 늦게 끝나 저녁엔 가벼운 복습 블록 추천"
            level = "medium"
        else:
            note = "저녁 집중 블록 확보 가능"
            level = "high"
        windows.append({
            "date": date,
            "availability": level,
            "note": note,
            "session_count": len(items)
        })
    return windows


def milestone_to_task(assignment: Dict[str, Any], subject_id: str) -> List[Dict[str, Any]]:
    tasks = []
    base_due = assignment.get("hard_deadline")
    if assignment.get("start_at"):
        dt = assignment["start_at"]
        date, time = dt.split("T", 1)
        tasks.append({
            "id": f"task-{safe_id(assignment['id'] + '-start')}",
            "date": date,
            "startTime": time[:5],
            "duration": 45,
            "subjectId": subject_id,
            "stageId": "framework",
            "title": f"{assignment['name']} 시작",
            "memo": f"운영난이도 {assignment['difficulty_operational']} / 10 · {assignment['format']}",
            "completed": False,
            "createdAt": datetime.now().isoformat()
        })
    for idx, milestone in enumerate(assignment.get("milestones", []), start=1):
        due = milestone["due"]
        date, time = due.split("T", 1)
        tasks.append({
            "id": f"task-{safe_id(assignment['id'] + '-milestone-' + str(idx))}",
            "date": date,
            "startTime": time[:5],
            "duration": 40,
            "subjectId": subject_id,
            "stageId": "revise",
            "title": milestone["title"],
            "memo": assignment["name"],
            "completed": False,
            "createdAt": datetime.now().isoformat()
        })
    if base_due:
        date, time = base_due.split("T", 1)
        tasks.append({
            "id": f"task-{safe_id(assignment['id'] + '-deadline')}",
            "date": date,
            "startTime": time[:5],
            "duration": 30,
            "subjectId": subject_id,
            "stageId": "review",
            "title": f"{assignment['name']} 마감",
            "memo": f"hard deadline · 난이도 {assignment['difficulty_total']} / 10",
            "completed": False,
            "createdAt": datetime.now().isoformat()
        })
    return tasks


def session_to_calendar_event(session: Dict[str, Any]) -> Dict[str, Any]:
    note_lines = []
    if session.get("professor"):
        note_lines.append(f"교수님: {session['professor']} ({session['professor_score']}/10)")
    if session.get("summary"):
        easy = session["summary"].get("easy_explanation") if isinstance(session["summary"], dict) else None
        if easy:
            note_lines.append(easy)
    if session.get("raw_notes"):
        note_lines.append(f"원문메모 {min(len(session['raw_notes']), 3)}개 보존")
    return {
        "id": f"event-{session['id']}",
        "date": session["date"],
        "type": session["event_type"],
        "title": session["title"],
        "time": session["time_label"],
        "note": " · ".join(note_lines),
        "completed": False,
        "professor": session.get("professor"),
        "difficulty": session.get("difficulty"),
        "track": "B",
        "windowType": "clerkship-session"
    }


def assignment_to_calendar_events(assignment: Dict[str, Any]) -> List[Dict[str, Any]]:
    events = []
    if assignment.get("start_at"):
        date, time = assignment["start_at"].split("T", 1)
        events.append({
            "id": f"event-{safe_id(assignment['id'] + '-start')}",
            "date": date,
            "type": "assignment",
            "title": f"{assignment['name']} 착수",
            "time": time[:5],
            "note": f"운영 {assignment['difficulty_operational']}/10 · 내용 {assignment['difficulty_content']}/10",
            "completed": False,
            "difficulty": assignment.get("difficulty_total"),
            "track": "B",
            "windowType": "assignment-start"
        })
    if assignment.get("hard_deadline"):
        date, time = assignment["hard_deadline"].split("T", 1)
        event_type = "exam" if assignment.get("difficulty_total", 0) >= 8 else "assignment"
        events.append({
            "id": f"event-{safe_id(assignment['id'] + '-deadline')}",
            "date": date,
            "type": event_type,
            "title": f"{assignment['name']} 마감",
            "time": time[:5],
            "note": assignment.get("format") or assignment.get("raw_deadline") or "",
            "completed": False,
            "difficulty": assignment.get("difficulty_total"),
            "track": "B",
            "windowType": "assignment-deadline"
        })
    return events


def build_bundle(raw: Dict[str, Any], config: Dict[str, Any], rubric_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    audit = {
        "excluded_sessions": [],
        "unconfigured_assignments": [],
        "warnings": []
    }
    rubric = ProfessorRubric(rubric_data)
    sessions = normalize_sessions(raw, config, rubric, audit)
    assignments = build_assignments(raw, config, sessions, audit)
    daily_windows = build_daily_windows(sessions, config)
    bundle = {
        "meta": {
            "clerkship_id": config["meta"]["clerkship_id"],
            "subject": config["meta"]["subject"],
            "track": config["meta"]["track"],
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "raw_source": raw.get("meta", {}),
            "config_source": config.get("meta", {}),
            "rubric_source": rubric_data.get("meta", {})
        },
        "fixed_info": raw.get("fixed_info", {}),
        "source_override": raw.get("source_override", {}),
        "submission_rules_raw": raw.get("submission_rules_raw", []),
        "sessions": sessions,
        "assignments": assignments,
        "daily_windows": daily_windows,
        "professor_rubric": rubric_data.get("professors", {}),
        "audit": audit,
        "notes": {
            "render_policy": raw.get("render_policy_v15", {}),
            "final_pdf_plan": raw.get("final_pdf_plan_v14") or raw.get("final_pdf_plan_v13") or {},
            "reference_priority": raw.get("reference_priority_v12", {})
        }
    }
    return bundle, audit


def apply_bundle_to_planner(base_state: Dict[str, Any], bundle: Dict[str, Any]) -> Dict[str, Any]:
    state = copy.deepcopy(base_state)
    subjects = state.setdefault("subjects", [])
    tasks = state.setdefault("tasks", [])
    calendar_events = state.setdefault("calendarEvents", [])
    state["clerkshipBundles"] = state.get("clerkshipBundles", {})
    state["clerkshipBundles"][bundle["meta"]["clerkship_id"]] = bundle

    respiratory_subject = next((s for s in subjects if s.get("name") == "호흡기"), None)
    if respiratory_subject:
        respiratory_subject["note"] = (
            (respiratory_subject.get("note") or "")
            + "\n\n[호흡기내과 실습 import 적용] B트랙 일정/과제/교수님 난이도는 clerkship bundle 기준으로 본다."
        ).strip()
        respiratory_subject["recentHistory"] = [
            f"{datetime.now().month}/{datetime.now().day} (토) · 호흡기 실습 JSON import 적용",
            *(respiratory_subject.get("recentHistory") or [])
        ][:8]
        subject_id = respiratory_subject.get("id")
    else:
        subject_id = "subject-respiratory"

    existing_event_ids = {event.get("id") for event in calendar_events}
    for session in bundle["sessions"]:
        event = session_to_calendar_event(session)
        if event["id"] not in existing_event_ids:
            calendar_events.append(event)
            existing_event_ids.add(event["id"])
    for assignment in bundle["assignments"]:
        for event in assignment_to_calendar_events(assignment):
            if event["id"] not in existing_event_ids:
                calendar_events.append(event)
                existing_event_ids.add(event["id"])

    existing_task_ids = {task.get("id") for task in tasks}
    for assignment in bundle["assignments"]:
        for task in milestone_to_task(assignment, subject_id):
            if task["id"] not in existing_task_ids:
                tasks.append(task)
                existing_task_ids.add(task["id"])

    tasks.sort(key=lambda x: (x.get("date", "9999-99-99"), x.get("startTime", "99:99"), x.get("title", "")))
    calendar_events.sort(key=lambda x: (x.get("date", "9999-99-99"), x.get("time", "99:99"), x.get("title", "")))
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Build normalized clerkship bundle and planner import state")
    parser.add_argument("--raw", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--rubric", required=True)
    parser.add_argument("--base-state", required=True)
    parser.add_argument("--bundle-out", required=True)
    parser.add_argument("--planner-out", required=True)
    parser.add_argument("--audit-out", required=True)
    args = parser.parse_args()

    raw = load_json(Path(args.raw))
    config = load_json(Path(args.config))
    rubric = load_json(Path(args.rubric))
    base_state = load_json(Path(args.base_state))

    bundle, audit = build_bundle(raw, config, rubric)
    planner_state = apply_bundle_to_planner(base_state, bundle)

    write_json(Path(args.bundle_out), bundle)
    write_json(Path(args.planner_out), planner_state)
    write_json(Path(args.audit_out), audit)

    print("bundle:", args.bundle_out)
    print("planner:", args.planner_out)
    print("audit:", args.audit_out)


if __name__ == "__main__":
    main()
