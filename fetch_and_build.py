#!/usr/bin/env python3
"""
digiicampus -> ics, live-fetch version.

pulls a rolling window (today -> +56 days) directly from the real api,
using AUTH_TOKEN and COOKIE from environment variables (injected via
github actions secrets, never committed to the repo).

your weekly job: grab a fresh Auth-Token + Cookie from browser devtools
(same way you did the first time) and update the two github secrets:
  DIGIICAMPUS_AUTH_TOKEN
  DIGIICAMPUS_COOKIE

then either wait for the scheduled run or trigger it manually from the
Actions tab. that's the entire manual step. thirty seconds, once a week.
"""
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone

CLASS_IDS = [2467, 2484, 2495, 2508, 2519, 2530, 3597, 3979]
BASE_URL = "https://skcet.digiicampus.com/rest/classes/v2/lessons"
WINDOW_DAYS_BACK = 3     # small buffer so "today" doesn't fall off the edge
WINDOW_DAYS_FORWARD = 56  # ~8 weeks forward, plenty of runway between refreshes


def build_request_url():
    now = datetime.now()
    start = now - timedelta(days=WINDOW_DAYS_BACK)
    end = now + timedelta(days=WINDOW_DAYS_FORWARD)
    params = [("classIds", str(cid)) for cid in CLASS_IDS]
    params.append(("from", start.strftime("%Y-%m-%d 00:00:00")))
    params.append(("to", end.strftime("%Y-%m-%d 23:59:59")))
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def fetch_lessons(auth_token, cookie):
    url = build_request_url()
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json, text/plain, */*")
    req.add_header("Auth-Token", auth_token)
    req.add_header("Cookie", cookie)
    req.add_header(
        "User-Agent",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/26.5 Safari/605.1.15",
    )
    req.add_header("Referer", "https://skcet.digiicampus.com/calendar")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(
            f"api call failed with HTTP {e.code}. "
            f"most likely cause: your Auth-Token/Cookie secrets are stale or wrong. "
            f"go refresh them. response body: {body[:500]}"
        )
    except Exception as e:
        raise SystemExit(f"api call failed outright: {e}")

    if status != 200:
        raise SystemExit(f"unexpected status {status}, aborting rather than writing garbage")

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise SystemExit(
            "response wasn't valid json — this usually means the token expired "
            "and digicampus handed back a login page instead of data. refresh the token."
        )

    if not isinstance(data, list):
        raise SystemExit(f"expected a json array of lessons, got: {type(data)}")

    return data


def fold_line(line, limit=73):
    if len(line) <= limit:
        return line
    parts = [line[:limit]]
    rest = line[limit:]
    while rest:
        parts.append(" " + rest[: limit - 1])
        rest = rest[limit - 1 :]
    return "\r\n".join(parts)


def escape_text(text):
    if not text:
        return ""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def parse_dt(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def build_ics(lessons, calendar_name="SKCET Timetable"):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//mish//digiicampus-sync//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_text(calendar_name)}",
        "X-WR-TIMEZONE:Asia/Kolkata",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]

    now_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    skipped = 0

    for lesson in lessons:
        class_info = (lesson.get("classList") or [{}])[0]
        faculty_info_list = lesson.get("facultyList") or []
        faculty_names = ", ".join(
            f.get("facultyName", "").strip() for f in faculty_info_list if f.get("facultyName")
        )

        course_name = class_info.get("courseName") or "Untitled Lesson"
        course_code = class_info.get("courseCode") or ""
        batch = class_info.get("batch") or ""
        dept = class_info.get("departmentName") or ""

        start_raw = lesson.get("start")
        end_raw = lesson.get("end")
        if not start_raw or not end_raw:
            skipped += 1
            continue

        dtstart = parse_dt(start_raw)
        dtend = parse_dt(end_raw)

        summary = course_name
        if course_code:
            summary = f"{course_name} ({course_code})"

        is_cancelled = bool(lesson.get("isCancelled"))
        status = "CANCELLED" if is_cancelled else "CONFIRMED"
        if is_cancelled:
            summary = f"CANCELLED: {summary}"

        desc_parts = []
        if faculty_names:
            desc_parts.append(f"Faculty: {faculty_names}")
        if batch:
            desc_parts.append(f"Batch: {batch}")
        if dept:
            desc_parts.append(f"Dept: {dept}")
        description = escape_text("\n".join(desc_parts))

        lesson_id = lesson.get("id")
        uid = f"digiicampus-lesson-{lesson_id}@mish-timetable"

        lines.append("BEGIN:VEVENT")
        lines.append(fold_line(f"UID:{uid}"))
        lines.append(f"DTSTAMP:{now_utc}")
        lines.append(f"DTSTART;TZID=Asia/Kolkata:{dtstart.strftime('%Y%m%dT%H%M%S')}")
        lines.append(f"DTEND;TZID=Asia/Kolkata:{dtend.strftime('%Y%m%dT%H%M%S')}")
        lines.append(fold_line(f"SUMMARY:{escape_text(summary)}"))
        if description:
            lines.append(fold_line(f"DESCRIPTION:{description}"))
        lines.append(f"STATUS:{status}")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n", skipped


def main():
    auth_token = os.environ.get("DIGIICAMPUS_AUTH_TOKEN")
    cookie = os.environ.get("DIGIICAMPUS_COOKIE")

    if not auth_token or not cookie:
        raise SystemExit(
            "missing DIGIICAMPUS_AUTH_TOKEN or DIGIICAMPUS_COOKIE env vars. "
            "set them as github actions secrets, this script won't run without them."
        )

    lessons = fetch_lessons(auth_token, cookie)
    ics_content, skipped = build_ics(lessons)

    output_path = "docs/timetable.ics"
    os.makedirs("docs", exist_ok=True)
    with open(output_path, "w", newline="") as f:
        f.write(ics_content)

    print(f"fetched {len(lessons)} lessons, wrote {len(lessons) - skipped} events, {skipped} skipped")


if __name__ == "__main__":
    main()
