#!/usr/bin/env python3

import argparse
from datetime import UTC, datetime
from pathlib import Path

CATEGORY_ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]


def format_skill_list(skills: list[str]) -> str:
    quoted = [f"`{skill}`" for skill in sorted(set(skills))]
    if len(quoted) == 1:
        return quoted[0]
    if len(quoted) == 2:
        return f"{quoted[0]} and {quoted[1]}"
    return f"{', '.join(quoted[:-1])}, and {quoted[-1]}"


def add_entry(lines: list[str], date: str, entry: str) -> list[str]:
    date_header = f"## [{date}]"

    try:
        date_start = lines.index(date_header)
    except ValueError:
        next_date = next(
            (index for index, line in enumerate(lines) if line.startswith("## [")),
            len(lines),
        )
        block = [date_header, "", "### Changed", "", entry, ""]
        return lines[:next_date] + block + lines[next_date:]

    date_end = next(
        (
            index
            for index in range(date_start + 1, len(lines))
            if lines[index].startswith("## [")
        ),
        len(lines),
    )
    if entry in lines[date_start:date_end]:
        return lines

    changed_header = "### Changed"
    try:
        changed_start = lines.index(changed_header, date_start + 1, date_end)
    except ValueError:
        section_headers = [
            (index, line.removeprefix("### "))
            for index, line in enumerate(
                lines[date_start + 1 : date_end], date_start + 1
            )
            if line.startswith("### ")
        ]
        insert_at = next(
            (
                index
                for index, category in section_headers
                if category in CATEGORY_ORDER
                and CATEGORY_ORDER.index(category) > CATEGORY_ORDER.index("Changed")
            ),
            date_end,
        )
        block = ["### Changed", "", entry, ""]
        if insert_at > 0 and lines[insert_at - 1]:
            block.insert(0, "")
        return lines[:insert_at] + block + lines[insert_at:]

    insert_at = changed_start + 1
    if insert_at == len(lines) or lines[insert_at]:
        lines.insert(insert_at, "")
        insert_at += 1
    else:
        insert_at += 1
    lines.insert(insert_at, entry)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a dated upstream skill sync entry to CHANGELOG.md."
    )
    parser.add_argument("skills", nargs="+", help="Category-qualified skill names.")
    parser.add_argument(
        "--file", type=Path, default=Path("CHANGELOG.md"), help="Changelog path."
    )
    parser.add_argument(
        "--date",
        default=datetime.now(UTC).date().isoformat(),
        help="ISO 8601 date. Defaults to the current UTC date.",
    )
    arguments = parser.parse_args()

    skill_list = format_skill_list(arguments.skills)
    source = "repository" if len(set(arguments.skills)) == 1 else "repositories"
    entry = (
        f"- Upstream skill sync: refresh {skill_list} from the declared source "
        f"{source}."
    )

    lines = arguments.file.read_text().splitlines()
    updated = add_entry(lines, arguments.date, entry)
    arguments.file.write_text("\n".join(updated).rstrip() + "\n")


if __name__ == "__main__":
    main()
