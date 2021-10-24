import typing as t

import strawberry as s


@s.type
class Question:
    question: str
    valid_answers: t.List[str]
    meaning: str


@s.type
class Exam:
    name: str
    num_questions: int
    max_wrong: t.Optional[int]
    timelimit: int
    hsk_level: int
    deck: t.List[Question]


@s.input
class NewQuestion:
    question: str
    valid_answers: t.List[str]
    meaning: str


@s.input
class NewExam:
    name: str
    num_questions: int
    max_wrong: t.Optional[int]
    timelimit: int
    hsk_level: int
    deck: t.List[NewQuestion]


@s.input
class NewCard:
    question: str
    meaning: str
    valid_answers: t.List[str]


@s.type
class ExamMutation:
    name: str

    @s.field
    async def add_cards(self, info, cards: t.List[NewCard]) -> bool:
        exam = info.context.store.load_exam(self.name)
        for card in cards:
            new_question = Question(
                question=card.question,
                meaning=card.meaning,
                valid_answers=card.valid_answers,
            )

            assert card.question not in [q.question for q in exam.deck], f'Question {card.question}already exists.'
            exam.deck.append(new_question)

        info.context.store.store_exam(exam)
        return True

    @s.field
    async def remove_card(self, info, question: str) -> bool:
        exam = info.context.store.load_exam(self.name)
        assert question in [q.question for q in exam.deck], "Question doesn't exists."

        exam.deck = [q for q in exam.deck if q.question != question]
        info.context.store.store_exam(exam)
        return True

    @s.field
    async def edit_card(
        self,
        info,
        question: str,
        new_question: t.Optional[str] = None,
        new_valid_answers: t.Optional[t.List[str]] = None,
        new_meaning: t.Optional[str] = None,
    ) -> bool:
        exam = info.context.store.load_exam(self.name)
        assert question in [q.question for q in exam.deck], "Question doesn't exists."
        index = [q.question for q in exam.deck].index(question)
        card = exam.deck[index]

        if new_question is not None:
            card.question = new_question

        if new_valid_answers is not None:
            card.valid_answers = new_valid_answers

        if new_meaning is not None:
            card.meaning = new_meaning

        info.context.store.store_exam(exam)
        return True
