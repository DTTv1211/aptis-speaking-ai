"""Question bank synchronized with DTTv1211/aptis-speaking-ai."""

import json
import re
from pathlib import Path
from typing import Any


APP_DIR = Path(__file__).resolve().parent


def _load_list(filename: str) -> list[dict[str, Any]]:
    with (APP_DIR / filename).open("r", encoding="utf-8") as data_file:
        data = json.load(data_file)
    if not isinstance(data, list) or not data:
        raise ValueError(f"{filename} phải là một danh sách đề không rỗng.")
    return data


def _validate_common_ids(items: list[dict[str, Any]], filename: str) -> None:
    seen_ids: set[int] = set()
    for position, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"{filename}: đề tại vị trí {position} không hợp lệ.")
        item_id = item.get("id")
        if not isinstance(item_id, int) or item_id in seen_ids:
            raise ValueError(f"{filename}: id tại vị trí {position} không hợp lệ/trùng lặp.")
        seen_ids.add(item_id)


def _validate_three_question_sets(
    items: list[dict[str, Any]], filename: str, image_key: str
) -> None:
    _validate_common_ids(items, filename)
    for item in items:
        images = item.get(image_key)
        if image_key == "images":
            if not isinstance(images, list) or len(images) not in {1, 2}:
                raise ValueError(f"{filename}: đề {item['id']} phải có 1 hoặc 2 ảnh.")
            if not all(isinstance(image, str) and image.strip() for image in images):
                raise ValueError(f"{filename}: đề {item['id']} chứa ảnh không hợp lệ.")
        elif not isinstance(images, str) or not images.strip():
            raise ValueError(f"{filename}: đề {item['id']} thiếu ảnh.")

        questions = item.get("questions")
        if (
            not isinstance(questions, list)
            or len(questions) != 3
            or not all(isinstance(question, str) and question.strip() for question in questions)
        ):
            raise ValueError(f"{filename}: đề {item['id']} phải có đúng 3 câu hỏi.")


PART1_DATA = _load_list("part1.json")
_validate_common_ids(PART1_DATA, "part1.json")
if not all(isinstance(item.get("question"), str) and item["question"].strip() for item in PART1_DATA):
    raise ValueError("part1.json chứa câu hỏi không hợp lệ.")

PART2_DATA = _load_list("part2.json")
_validate_three_question_sets(PART2_DATA, "part2.json", "image")

PART3_DATA = _load_list("part3.json")
_validate_three_question_sets(PART3_DATA, "part3.json", "images")

PART4_DATA = _load_list("part4.json")
_validate_common_ids(PART4_DATA, "part4.json")
if not all(isinstance(item.get("question"), str) and item["question"].strip() for item in PART4_DATA):
    raise ValueError("part4.json chứa câu hỏi không hợp lệ.")


def part4_questions(question_block: str) -> list[str]:
    """Convert the numbered long-turn block into evaluator-ready questions."""
    return [
        re.sub(r"^\s*\d+\.\s*", "", line).strip()
        for line in question_block.splitlines()
        if line.strip()
    ]
