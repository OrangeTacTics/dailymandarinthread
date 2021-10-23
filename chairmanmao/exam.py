from __future__ import annotations
import typing as t
from dataclasses import dataclass
from random import Random, getrandbits
from enum import Enum

from .types import Exam, Question


class TickResult(Enum):
    nothing = "nothing"
    timeout = "timeout"
    next_question = "next_question"
    pause = "pause"
    finished = "finished"


@dataclass
class Examiner:
    # Constants
    exam: Exam
    questions: t.List[Question]
    max_wrong: t.Optional[int]
    timelimit: int
    fail_on_timeout: bool
    practice: bool

    # Variables
    current_question_index: int
    current_question_time_left: int
    answers_given: t.List[Answer]
    pause_time: int

    @staticmethod
    def make(
        exam: Exam,
        *,
        practice: bool = False,
        seed: t.Optional[int] = None,
    ) -> Examiner:
        questions = list(exam.deck)

        if not practice:
            questions = questions[: exam.num_questions]

        if seed is None:
            seed = getrandbits(64)

        random_generator = Random(seed)
        random_generator.shuffle(questions)

        timelimit = exam.timelimit if not practice else 30

        return Examiner(
            exam=exam,
            questions=questions,
            max_wrong=exam.max_wrong if not practice else None,
            timelimit=timelimit,
            fail_on_timeout=practice,
            practice=practice,
            current_question_index=-1,
            current_question_time_left=timelimit,
            answers_given=[],
            pause_time=0,
        )

    ####################################################################
    # Queries
    ####################################################################

    def ready_for_next_question(self) -> bool:
        return self.current_question_index + 1 == len(self.answers_given)

    def ready_for_next_answer(self) -> bool:
        return self.current_question_index == len(self.answers_given)

    def current_question(self) -> Question:
        assert self.current_question_index >= 0, "You must call tick() before the first question."
        # TODO Handle case where current_question_index > len(self.questions)
        return self.questions[self.current_question_index]

    def previous_answer(self) -> Answer:
        return self.answers_given[-1]

    def score(self) -> float:
        num_questions_answered = len(self.answers_given)
        return 1.0 - self.number_wrong() / num_questions_answered

    def passed(self) -> bool:
        assert self.finished(), "Exam is not finished"
        return not self._gave_up() and self.max_wrong is not None and self.number_wrong() <= self.max_wrong

    def _gave_up(self) -> bool:
        return any(isinstance(a, Quit) for a in self.answers_given)

    def finished(self) -> bool:
        return (
            self._finished_gave_up()
            or self._finished_too_many_wrong()
            or self._finished_all_questions_answered()
            or self._finished_timeout()
        )

    def _finished_gave_up(self) -> bool:
        return any(isinstance(a, Quit) for a in self.answers_given)

    def _finished_too_many_wrong(self) -> bool:
        return self.max_wrong is not None and self.number_wrong() > self.max_wrong

    def _finished_all_questions_answered(self) -> bool:
        return len(self.answers_given) == len(self.questions)

    def _finished_timeout(self) -> bool:
        return self.fail_on_timeout and self._number_timeouts() > 0

    def _number_timeouts(self) -> int:
        number_timeout = 0
        for answer in self.answers_given:
            if isinstance(answer, Timeout):
                number_timeout += 1

        return number_timeout

    def number_wrong(self) -> int:
        num_questions_answered = len(self.answers_given)
        questions = self.questions[:num_questions_answered]

        number_wrong = 0

        for question, answer in zip(questions, self.answers_given):
            if not isinstance(answer, Correct):
                number_wrong += 1

        return number_wrong

    def grade(self) -> t.List[t.Tuple[Question, Answer]]:
        num_questions_answered = len(self.answers_given)
        questions = self.questions[:num_questions_answered]

        results = []

        for question, answer in zip(questions, self.answers_given):
            results.append((question, answer))

        return results

    def timed_out(self) -> bool:
        return self.current_question_time_left <= 0

    ####################################################################
    # Actions
    ####################################################################

    def tick(self) -> TickResult:
        if self.finished():
            return TickResult.finished
        elif self.pause_time > 0:
            self.pause_time -= 1
            return TickResult.pause
        elif self.ready_for_next_question():
            self.current_question_index += 1
            self.current_question_time_left = self.timelimit
            return TickResult.next_question
        elif self.timed_out():
            self.answers_given.append(Timeout())
            self.pause_time = 2
            return TickResult.timeout
        else:
            self.current_question_time_left -= 1
            return TickResult.nothing

    def answer(self, answer: str) -> bool:
        assert not self.finished()
        assert self.ready_for_next_answer(), "Can't answer again until the next tick."
        current_question = self.current_question()

        correct = answer.lower() in current_question.valid_answers

        if correct:
            self.answers_given.append(Correct(answer))
        else:
            self.answers_given.append(Incorrect(answer))

        return correct

    def give_up(self) -> None:
        assert self.ready_for_next_answer(), "Can't give_up until the next tick."
        self.answers_given.append(Quit())


@dataclass
class Timeout:
    def __str__(self) -> str:
        return "*timed out*"


@dataclass
class Quit:
    def __str__(self) -> str:
        return "*gave up*"


@dataclass
class Correct:
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass
class Incorrect:
    value: str

    def __str__(self) -> str:
        return self.value


Answer = t.Union[Correct, Incorrect, Timeout, Quit]


def make_hsk1_exam() -> Exam:
    import csv

    deck = []

    with open("data/decks/hsk1.csv") as infile:
        fieldnames = ["question", "answers", "meaning", "unused"]
        reader = csv.DictReader(infile, fieldnames=fieldnames)

        for word in reader:
            deck.append(Question(word["question"], word["answers"].split(","), word["meaning"]))

    return Exam(
        name="HSK 1",
        deck=deck,
        num_questions=10,
        max_wrong=2,
        timelimit=10,
        hsk_level=1,
    )


def _random_run(seed: int):
    import time

    r = Random(seed)

    exam = make_hsk1_exam()
    active_exam = Examiner.make(exam, practice=False, seed=1)
    done = False
    while not done:
        k = r.randint(1, 15)
        for n in range(k):
            result = active_exam.tick()
            if result == TickResult.nothing:
                pass
            elif result == TickResult.timeout:
                print("Timeout")
            elif result == TickResult.next_question:
                print("Next question")
                pass
            elif result == TickResult.finished:
                print("Done!")
                done = True

            if not done:
                question = active_exam.current_question()
                if r.randint(1, 100) < 90:
                    answer = question.valid_answers[0]
                else:
                    answer = "."

                active_exam.answer(answer)
                print()
                time.sleep(0.1)

    for q, a in active_exam.grade():
        print(q.question, repr(a))
    print()


def test_timeout():
    exam = make_hsk1_exam()
    active_exam = Examiner.make(exam, practice=False, seed=1)

    active_exam.tick()
    active_exam.current_question()

    for _ in range(active_exam.timelimit):
        r = active_exam.tick()
        assert r == TickResult.nothing

    r = active_exam.tick()
    assert r == TickResult.timeout


if __name__ == "__main__":
    test_timeout()
