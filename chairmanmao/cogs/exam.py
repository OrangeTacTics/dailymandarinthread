from __future__ import annotations
import typing as t
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import random
import csv

import discord
from discord.ext import commands, tasks

from chairmanmao.cogs import ChairmanMaoCog
from chairmanmao.types import Exam, Question


class ExamCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('ExamCog')
        self.loop.start()
        self.active_exam: t.Optional[ActiveExam] = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.active_exam:
            active_exam = self.active_exam
            if message.channel.id == active_exam.channel.id and message.author.id == active_exam.member.id:
                if not message.content.startswith('$') and active_exam.ready_for_next_answer():
                    await self.send_answer(active_exam, message)

    @tasks.loop(seconds=1)
    async def loop(self):
        if self.active_exam is not None:
            if self.active_exam.finished():
                self.active_exam = None

            elif self.active_exam.is_time_up():
                self.active_exam.timeout()

    @commands.group()
    async def exam(self, ctx):
        constants = self.chairmanmao.constants()
        if ctx.invoked_subcommand is None:
            exam_name = self.next_exam_for(ctx.author)
            if exam_name is None:
                await ctx.send('Available exams: ' + ' '.join(self.exam_names()))
                return

            if exam_name is not None:
                lines = [
                    f'The next exam you are scheduled to take is {exam_name}.',
                ]

                if ctx.channel.id == constants.exam_channel.id:
                    lines.append(f'To take the exam, use `$exam start`')
                else:
                    lines.append(f'To take the exam, go to {constants.exam_channel.mention} and use `$exam start`')

                await ctx.send('\n'.join(lines))

            else:
                await ctx.send(f'There are currently no exams ready for you.')

    @exam.command(name='list')
    async def cmd_exam_list(self, ctx):
#        exam_names = self.chairmanmao().api.get_exam_names()
        await ctx.send('Available exams: ' + ' '.join(self.exam_names()))

    @exam.command(name='start')
    async def cmd_exam_start(self, ctx, exam_name: t.Optional[str] = None):
        if exam_name is None:
            exam_name = self.next_exam_for(ctx.author)
            if exam_name is None:
                await ctx.send('Available exams: ' + ' '.join(self.exam_names()))
                return

        exam: t.Optional[Exam] = EXAMS.get(exam_name)

        if exam is None:
            await ctx.send('Available exams: ' + ' '.join(self.exam_names()))
            return

        constants = self.chairmanmao.constants()
        if ctx.channel.id != constants.exam_channel.id:
            await ctx.send(f'This command must be run in {constants.exam_channel.mention}')
            return

        if self.active_exam is not None:
            await ctx.send(f'{self.active_exam.member.mention} is currently taking an exam')
            return

        active_exam = self.create_active_exam(ctx.author, ctx.channel, exam)
        self.active_exam = active_exam
        await self.run_exam(active_exam)

    @exam.command(name='practice')
    async def cmd_exam_practice(self, ctx, exam_name: t.Optional[str] = None):
        if exam_name is None:
            exam_name = self.next_exam_for(ctx.author)
            if exam_name is None:
                await ctx.send('Available exams: ' + ' '.join(self.exam_names()))
                return

        exam: t.Optional[Exam] = EXAMS.get(exam_name)

        if exam is None:
            await ctx.send('Available exams: ' + ' '.join(self.exam_names()))
            return

        constants = self.chairmanmao.constants()
        if ctx.channel.id != constants.exam_channel.id:
            await ctx.send(f'This command must be run in {constants.exam_channel.mention}')
            return

        if self.active_exam is not None:
            await ctx.send(f'{self.active_exam.member.mention} is currently taking an exam')
            return

        active_exam = self.create_active_exam(ctx.author, ctx.channel, exam, practice=True)
        self.active_exam = active_exam
        await self.run_exam(active_exam)

    @exam.command(name='quit')
    async def cmd_exam_quit(self, ctx):
        constants = self.chairmanmao.constants()
        if ctx.channel.id != constants.exam_channel.id:
            await ctx.send(f'This command must be run in {constants.exam_channel.mention}')
            return

        if self.active_exam is None:
#            await ctx.send(f'There is no exam in progress.')
            return

        if self.active_exam.member.id != ctx.author.id:
#            await ctx.send(f"The exam in progress isn't yours")
            return

        self.active_exam.give_up()
#        await ctx.message.add_reaction(constants.dekinai_emoji)

    def next_exam_for(self, member: discord.Member) -> t.Optional[str]:
        current_hsk = self.chairmanmao.api.get_hsk(member.id)
        if current_hsk is None:
            return 'hsk1'
        else:
            exam_name = f'hsk{current_hsk+1}'
            if exam_name in EXAMS:
                return exam_name
            else:
                return None

    def exam_names(self) -> t.List[str]:
        return sorted(EXAMS.keys())

    def create_active_exam(self, member: discord.Member, channel: discord.TextChannel, exam: Exam, practice: bool = False) -> ActiveExam:
        return ActiveExam.make(
            member=member,
            channel=channel,
            exam=exam,
            practice=practice,
        )

    async def run_exam(self, active_exam: ActiveExam) -> None:
        await self.send_exam_start_embed(active_exam)

        while not active_exam.finished():
            await self.send_next_question(active_exam)
            answer = await self.receive_answer(active_exam)

            await self.reply_to_answer(active_exam, answer)

        await self.show_results(active_exam)
        await self.reward(active_exam)

    async def receive_answer(self, active_exam: ActiveExam) -> Answer:
        while not active_exam.ready_for_next_question():
            await asyncio.sleep(0)

        return active_exam.previous_answer()

    async def reply_to_answer(self, active_exam: ActiveExam, answer: Answer) -> None:
        constants = self.chairmanmao.constants()
        question = active_exam.current_question()

        if isinstance(answer, Correct):
            emoji = '✅'
            color = 0x00ff00
            correct_answer = f'{question.valid_answers[0]}'
        elif isinstance(answer, Incorrect):
            emoji = '❌'
            color = 0xff0000
            correct_answer = f'{answer} → {question.valid_answers[0]}'
        elif isinstance(answer, Timeout):
            emoji = '⏲️'
            color = 0xd0deec
            correct_answer = f'{question.valid_answers[0]}'
        else: # isinstance(answer, Quit):
            emoji = constants.dekinai_emoji
            color = 0xffdbac
            correct_answer = f'{question.valid_answers[0]}'

        description = f'{emoji}　{question.question}　　{correct_answer}　　*{question.meaning}*'

        embed = discord.Embed(
            description=description,
            color=color,
        )
        await active_exam.channel.send(embed=embed)

        if isinstance(answer, Timeout) and not active_exam.finished():
            await asyncio.sleep(1.5)

    async def send_exam_start_embed(self, active_exam: ActiveExam) -> None:
        exam = active_exam.exam

#        description = f'{exam.name}'

        embed = discord.Embed(
#            title='ActiveExam',
#            description=description,
            color=0xffa500,
        )

        embed.set_author(
            name=active_exam.member.display_name,
            icon_url=active_exam.member.avatar_url,
        )
        embed.add_field(
            name='Deck',
            value=exam.name,
            inline=True,
        )

        embed.add_field(
            name='Questions',
            value=f'{exam.num_questions}',
            inline=True,
        )

        embed.add_field(
            name='Time Limit',
            value=f'{active_exam.timelimit} seconds',
            inline=False,
        )
        if active_exam.max_wrong is not None:
            embed.add_field(
                name='Mistakes Allowed',
                value=f'{active_exam.max_wrong}',
                inline=True,
            )

        await active_exam.channel.send(embed=embed)

    async def send_answer(self, active_exam: ActiveExam, message: discord.Message) -> None:
        correct = active_exam.answer(message.content.strip())  # noqa
#        if correct:
#            await message.add_reaction('✅')
#        else:
#            await message.add_reaction('❌')

    async def send_next_question(self, active_exam: ActiveExam) -> None:
        question = active_exam.load_next_question()

        font = 'kuaile'
        size = 64
        color = (255, 0, 0)
        image_buffer = self.chairmanmao.draw_manager.draw(
            font,
            question.question,
            size=size,
            color=color,
        )
        filename = 'hanzi_' + '_'.join('u' + hex(ord(char))[2:] for char in question.question) + '.png'
        file = discord.File(fp=image_buffer, filename=filename)
        await active_exam.channel.send(file=file)
        self.chairmanmao.logger.info(f'{question.question}　　{question.valid_answers[0]}')

    async def show_results(self, active_exam: ActiveExam) -> None:
        lines = []

        # if is not practice
        if not active_exam.fail_on_timeout:
            questions_answered = active_exam.questions[:len(active_exam.answers_given)]
            longest_answer = max(len(question.question) for question in questions_answered)

            for question, answer in active_exam.grade():
                correct = isinstance(answer, Correct)
                emoji = '✅' if correct else '❌'
                correct_answer = question.valid_answers[0]
                question_str = (question.question).ljust(longest_answer + 2, '　')
                answer_str = answer if correct else f'{answer} → {correct_answer}'
                lines.append(f'{emoji}　{question_str} {answer_str}　*{question.meaning}*')

            if active_exam.passed():
                title = 'ActiveExam Passed: ' + active_exam.exam.name
                color = 0x00ff00
            else:
                title = 'ActiveExam Failed: ' + active_exam.exam.name
                color = 0xff0000

            embed = discord.Embed(
                title=title,
                description='\n'.join(lines),
                color=color,
            )
            embed.set_author(
                name=active_exam.member.display_name,
                icon_url=active_exam.member.avatar_url,
            )
            if active_exam.passed() and active_exam.max_wrong is not None and active_exam.max_wrong > 0:
                score = active_exam.score() * 100
                embed.add_field(name='Score', value=f'{score:2.1f}%', inline=True)

        # if is practice
        else:
            questions_answered = active_exam.questions[:len(active_exam.answers_given)]
            longest_answer = max(len(question.question) for question in questions_answered)

            title = 'ActiveExam Practice: ' + active_exam.exam.name
            color = 0x00ff00

            sampled_corrections = [(q, a) for (q, a) in active_exam.grade() if isinstance(a, Incorrect)]
            while len(sampled_corrections) > 5:
                sampled_corrections.pop(random.randrange(len(sampled_corrections)))

            for question, answer in sampled_corrections:
                correct = isinstance(answer, Correct)
                emoji = '✅' if correct else '❌'
                correct_answer = question.valid_answers[0]
                question_str = (question.question).ljust(longest_answer + 2, '　')
                answer_str = answer if correct else f'{answer} → {correct_answer}'
                lines.append(f'{emoji}　{question_str} {answer_str}　*{question.meaning}*')

            embed = discord.Embed(
                title=title,
                description='\n'.join(lines),
                color=color,
            )
            embed.set_author(
                name=active_exam.member.display_name,
                icon_url=active_exam.member.avatar_url,
            )
            score = active_exam.score() * 100
            embed.add_field(name='Score', value=f'{score:2.1f}%', inline=True)

        await active_exam.channel.send(embed=embed)

    async def reward(self, active_exam: ActiveExam) -> None:
        if active_exam.practice:
            return

        current_hsk = self.chairmanmao.api.get_hsk(active_exam.member.id)
        if current_hsk is not None and current_hsk >= active_exam.exam.hsk_level:
            return

        if active_exam.passed():
            username = self.chairmanmao.member_to_username(active_exam.member)

            self.chairmanmao.api.set_hsk(active_exam.member.id, active_exam.exam.hsk_level)
            self.chairmanmao.queue_member_update(active_exam.member.id)
            self.chairmanmao.logger.info(f'User {username} passed HSK {active_exam.exam.hsk_level}.')
            constants = self.chairmanmao.constants()
            await constants.commentators_channel.send(f'{username} passed the HSK {active_exam.exam.hsk_level} exam.')


def make_hsk1_exam() -> Exam:
    deck = []

    with open('data/decks/hsk1.csv') as infile:
        fieldnames = ['question', 'answers', 'meaning', 'unused']
        reader = csv.DictReader(infile, fieldnames=fieldnames)

        for word in reader:
            deck.append(Question(word['question'], word['answers'].split(','), word['meaning']))

    return Exam(
        name='HSK 1',
        deck=deck,
        num_questions=10,
        max_wrong=2,
        timelimit=10,
        hsk_level=1,
    )


def make_hsk2_exam() -> Exam:
    deck = []

    with open('data/decks/hsk2.csv') as infile:
        fieldnames = ['question', 'answers', 'meaning', 'unused']
        reader = csv.DictReader(infile, fieldnames=fieldnames)

        for word in reader:
            deck.append(Question(word['question'], word['answers'].split(','), word['meaning']))

    return Exam(
        name='HSK 2',
        deck=deck,
        num_questions=15,
        max_wrong=2,
        timelimit=8,
        hsk_level=2,
    )


def make_hsk3_exam() -> Exam:
    deck = []

    with open('data/decks/hsk3.csv') as infile:
        fieldnames = ['question', 'answers', 'meaning', 'unused']
        reader = csv.DictReader(infile, fieldnames=fieldnames)

        for word in reader:
            deck.append(Question(word['question'], word['answers'].split(','), word['meaning']))

    return Exam(
        name='HSK 3',
        deck=deck,
        num_questions=20,
        max_wrong=2,
        timelimit=7,
        hsk_level=3,
    )


EXAMS = {
    'hsk1': make_hsk1_exam(),
    'hsk2': make_hsk2_exam(),
    'hsk3': make_hsk3_exam(),
}


@dataclass
class ActiveExam:
    member: discord.Member
    channel: discord.TextChannel
    questions: t.List[Question]
    exam: Exam

    max_wrong: t.Optional[int]
    timelimit: int
    fail_on_timeout: bool
    practice: bool

    exam_start: datetime

    current_question_index: int
    current_question_start: datetime

    answers_given: t.List[Answer]

    @staticmethod
    def make(member: discord.Member, channel: discord.TextChannel, exam: Exam, practice: bool) -> ActiveExam:
        questions = list(exam.deck)
        random.shuffle(questions)

        if not practice:
            questions = questions[:exam.num_questions]

        now = datetime.now(timezone.utc).replace(microsecond=0)

        return ActiveExam(
            member=member,
            channel=channel,
            exam=exam,
            questions=questions,

            max_wrong=exam.max_wrong if not practice else None,
            timelimit=exam.timelimit if not practice else 30,
            fail_on_timeout=practice,
            practice=practice,

            exam_start=now,
            current_question_index=-1, # -1 because we need to call load_next_question() as least once.
            current_question_start=now,
            answers_given=[],
        )

    # queries
    def ready_for_next_question(self) -> bool:
        return len(self.answers_given) == self.current_question_index + 1

    def ready_for_next_answer(self) -> bool:
        return len(self.answers_given) == self.current_question_index

    def current_question(self) -> Question:
        return self.questions[self.current_question_index]

    def previous_answer(self) -> Answer:
        return self.answers_given[-1]

    def is_time_up(self) -> bool:
        if not self.ready_for_next_answer():
            return False

        now = datetime.now(timezone.utc).replace(microsecond=0)
        duration = now - self.current_question_start
        return duration.total_seconds() > self.timelimit

    def score(self) -> float:
        num_questions_answered = len(self.answers_given)
        return 1.0 - self.number_wrong() / num_questions_answered

    def gave_up(self) -> bool:
        return any(isinstance(a, Quit) for a in self.answers_given)

    def passed(self) -> bool:
        assert self.finished(), 'Exam is not finished'
        return not self.gave_up() and self.max_wrong is not None and self.number_wrong() <= self.max_wrong

    def number_timeouts(self) -> int:
        number_timeout = 0
        for answer in self.answers_given:
            if isinstance(answer, Timeout):
                number_timeout += 1

        return number_timeout

    def _finished_too_many_wrong(self) -> bool:
        return self.max_wrong is not None and self.number_wrong() > self.max_wrong

    def _finished_all_questions_answered(self) -> bool:
        return len(self.answers_given) == len(self.questions)

    def _finished_timeout(self) -> bool:
        return self.fail_on_timeout and self.number_timeouts() > 0

    def finished(self) -> bool:
        return (
            self.gave_up() or
            self._finished_too_many_wrong() or
            self._finished_all_questions_answered() or
            self._finished_timeout()
        )

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

    # actions

    def load_next_question(self) -> Question:
        assert not self.finished()
        now = datetime.now(timezone.utc)

        self.current_question_start = now
        self.current_question_index += 1

        question = self.questions[self.current_question_index]
        return question

    def answer(self, answer: str) -> bool:
        current_question = self.current_question()
        assert current_question, 'No question was asked'

        correct = answer.lower() in current_question.valid_answers

        if correct:
            self.answers_given.append(Correct(answer))
        else:
            self.answers_given.append(Incorrect(answer))

        return correct

    def timeout(self) -> None:
        self.answers_given.append(Timeout())

    def give_up(self) -> None:
        self.answers_given.append(Quit())


@dataclass
class Timeout:
    def __str__(self) -> str:
        return '*timed out*'


@dataclass
class Quit:
    def __str__(self) -> str:
        return '*gave up*'


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
