from __future__ import annotations
import typing as t
from dataclasses import dataclass
import asyncio
from enum import Enum

import discord
from discord.ext import commands, tasks

from chairmanmao.types import Profile
from chairmanmao.cogs import ChairmanMaoCog
from datetime import datetime, timezone

from chairmanmao.draw import DrawManager


class ExamCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('ExamCog')
        self.loop.start()
        self.active_exam: t.Optional[ActiveExam] = None

    @commands.Cog.listener()
    async def on_message(self, message):
        constants = self.chairmanmao.constants()
        if self.active_exam:
            active_exam = self.active_exam
            if message.channel.id == active_exam.channel.id and message.author.id == active_exam.member.id:
                if not message.content.startswith('$') and active_exam.ready_for_next_answer():
                    await self.answer_question(active_exam, message)

    @tasks.loop(seconds=1)
    async def loop(self):
        if self.active_exam is not None:
            if self.active_exam.finished():
                self.active_exam = None

            elif self.active_exam.is_time_up():
                self.active_exam.timeout()
                await self.active_exam.channel.send("⏲️ Time's up!")

    @commands.group()
    async def exam(self, ctx):
        constants = self.chairmanmao.constants()
        if ctx.invoked_subcommand is None:

            next_exam = make_exam()

            lines = [
                f'The next exam you are scheduled to take is {next_exam.name}.',
            ]

            if ctx.channel.id == constants.exam_channel.id:
                lines.append(f'To take the exam, use `$exam start`')
            else:
                lines.append(f'To take the exam, go to {constants.exam_channel.mention} and use `$exam start`')

            await ctx.send('\n'.join(lines))

    @exam.command(name='start')
    async def cmd_exam_start(self, ctx):
        constants = self.chairmanmao.constants()
        if ctx.channel.id != constants.exam_channel.id:
            await ctx.send(f'This command must be run in {constants.exam_channel.mention}')
            return

        if self.active_exam is not None:
            await ctx.send(f'{self.active_exam.member.mention} is currently taking an exam')
            return

        member = ctx.author
        channel = constants.exam_channel
        active_exam = ActiveExam.make(
            member=member,
            channel=channel,
            exam=make_exam(),
        )

        self.active_exam = active_exam

        exam = active_exam.exam

        description = f'{exam.name}'

        embed = discord.Embed(
#            title='Exam',
#            description=description,
            color=0xffa500,
        )

        embed.set_author(
            name=active_exam.member.display_name,
            icon_url=active_exam.member.avatar_url,
        )
        embed.add_field(
            name='Exam',
            value=exam.name,
            inline=True,
        )

        embed.add_field(
            name='Questions',
            value=f'{exam.num_questions()}',
            inline=True,
        )

        embed.add_field(
            name='Time Limit',
            value=f'{exam.timelimit} seconds',
            inline=False,
        )
        if exam.max_wrong > 0:
            embed.add_field(
                name='Mistakes Allowed',
                value=f'{exam.max_wrong}',
                inline=True,
            )

        await active_exam.channel.send(embed=embed)

        while not active_exam.finished():
            await self.send_next_question(active_exam)
            while not active_exam.ready_for_next_question():
                await asyncio.sleep(0)

        await self.show_results(active_exam)

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
        await ctx.message.add_reaction(constants.dekinai_emoji)

    async def send_next_question(self, active_exam: ActiveExam) -> None:
        question = active_exam.next_question()

        font = 'kuaile'
        image_buffer = self.chairmanmao.draw_manager.draw(font, question.question)
        filename = 'hanzi_' + '_'.join('u' + hex(ord(char))[2:] for char in question.question) + '.png'
        file = discord.File(fp=image_buffer, filename=filename)
        await active_exam.channel.send(file=file)

    async def answer_question(self, active_exam: ActiveExam, answer: discord.Message) -> None:
        correct = active_exam.answer(answer.content.strip())
        emoji = '✅' if correct else '❌'
        await answer.add_reaction(emoji)

#        if not correct:
#            await active_exam.channel.send('Correct answer: ' + current_question.valid_answers[0])

    async def show_results(self, active_exam: ActiveExam) -> None:
        lines = []

        questions_answered = active_exam.exam.questions[:len(active_exam.answers_given)]
        longest_answer = max(len(question.question) for question in questions_answered)

        for question, answer in active_exam.grade():
            correct = isinstance(answer, Correct)
            emoji = '✅' if correct else '❌'
            correct_answer = question.valid_answers[0]
            question_str = (question.question).ljust(longest_answer + 2, '　')
            answer_str = answer if correct else f'{answer} → {correct_answer}'
            lines.append(f'{emoji}　{question_str} {answer_str}　*{question.meaning}*')

        if active_exam.passed():
            title = 'Exam Passed: ' + active_exam.exam.name
            color = 0x00ff00
        else:
            title = 'Exam Failed: ' + active_exam.exam.name
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
        if active_exam.passed() and active_exam.exam.max_wrong > 0:
            score = active_exam.score() * 100
            embed.add_field(name='Score', value=f'{score:2.1f}%', inline=True)

        await active_exam.channel.send(embed=embed)



def make_exam() -> 'Exam':
    questions = []

    import csv
    import random
    with open('data/hsk1.csv') as infile:
        fieldnames = ['question', 'answers', 'meaning', 'unused']
        reader = csv.DictReader(infile, fieldnames=fieldnames)

        for word in reader:
            questions.append(ExamQuestion(word['question'], word['answers'].split(','), word['meaning']))

    random.shuffle(questions)
    questions = questions[:10]

    return Exam(
        name='HSK 1',
        questions=questions,
        max_wrong=2,
        timelimit=7,
    )


@dataclass
class ActiveExam:
    member: discord.Member
    channel: discord.TextChannel
    exam: Exam

    exam_start: datetime

    current_question_index: int
    current_question_start: datetime

    answers_given: t.List[Answer]

    @staticmethod
    def make(member: discord.Member, channel: discord.TextChannel, exam: Exam) -> ActiveExam:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        return ActiveExam(
                member=member,
                channel=channel,
                exam=exam,

                exam_start=now,
                current_question_index=-1, # -1 because we need to call next_question() as least once.
                current_question_start=now,
                answers_given=[],
            )

    def ready_for_next_question(self) -> bool:
        return len(self.answers_given) == self.current_question_index + 1

    def ready_for_next_answer(self) -> bool:
        return len(self.answers_given) == self.current_question_index

    def current_question(self) -> t.Optional[ExamQuestion]:
        try:
            return self.exam.questions[self.current_question_index]
        except:
            return None

    def next_question(self) -> ExamQuestion:
        assert not self.finished()
        now = datetime.now(timezone.utc)

        self.current_question_start = now
        self.current_question_index += 1

        question = self.exam.questions[self.current_question_index]
        return question

    def is_time_up(self) -> bool:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        duration = now - self.current_question_start
        return duration.total_seconds() > self.exam.timelimit

    def timeout(self) -> None:
        self.answers_given.append(Timeout())

    def give_up(self) -> None:
        self.answers_given.append(Quit())

    def answer(self, answer: str) -> bool:
        current_question = self.current_question()
        assert current_question, 'No question was asked'

        correct = answer.lower() in current_question.valid_answers

        if correct:
            self.answers_given.append(Correct(answer))
        else:
            self.answers_given.append(Incorrect(answer))

        return correct

    def score(self) -> float:
        num_questions_answered = len(self.answers_given)
        return 1.0 - self.number_wrong() / num_questions_answered

    def number_wrong(self) -> int:
        num_questions_answered = len(self.answers_given)
        questions = self.exam.questions[:num_questions_answered]

        number_wrong = 0

        for question, answer in zip(questions, self.answers_given):
            if not isinstance(answer, Correct):
                number_wrong += 1

        return number_wrong

    def grade(self) -> t.List[t.Tuple[ExamQuestion, Answer]]:
        num_questions_answered = len(self.answers_given)
        questions = self.exam.questions[:num_questions_answered]

        results = []

        for question, answer in zip(questions, self.answers_given):
            results.append((question, answer))

        return results

    def gave_up(self) -> bool:
        return any(isinstance(a, Quit) for a in self.answers_given)

    def passed(self) -> bool:
        assert self.finished(), 'Exam is not finished'
        return not self.gave_up() and self.number_wrong() <= self.exam.max_wrong

    def finished(self) -> bool:
        return (
            len(self.answers_given) == len(self.exam.questions) or  # complete
            self.number_wrong() > self.exam.max_wrong or            # missed too many questions
            self.gave_up()                                          # gave up
        )

    def last_question_was_timeout(self) -> bool:
        return len(self.answers_given) > 0 and isinstance(self.answers_given[-1], Timeout)


@dataclass
class Exam:
    name: str
    questions: t.List[ExamQuestion]
    max_wrong: int
    timelimit: int

    def num_questions(self):
        return len(self.questions)


@dataclass
class ExamQuestion:
    question: str
    valid_answers: t.List[str]
    meaning: str


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
