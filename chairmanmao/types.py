from __future__ import annotations
import typing as t
from dataclasses import dataclass


@dataclass
class Exam:
    name: str
    deck: t.List[Question]
    num_questions: int
    max_wrong: t.Optional[int]
    timelimit: int
    hsk_level: int


@dataclass
class Question:
    question: str
    valid_answers: t.List[str]
    meaning: str

    def is_correct(self, answer: str) -> bool:
        for valid_answer in self.valid_answers:
            answer_fixed = answer.lower().replace(" ", "").replace("5", "")
            valid_answer_fixed = valid_answer.lower().replace(" ", "").replace("5", "")
            if answer_fixed == valid_answer_fixed:
                return True

        return False


UserId = int
Json = t.Any
