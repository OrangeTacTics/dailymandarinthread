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
                    await active_exam.answer_question(message)

    @tasks.loop(seconds=1)
    async def loop(self):
        if self.active_exam is not None:
            if self.active_exam.finished:
                self.active_exam = None
            elif self.active_exam.is_time_up():
                await self.active_exam.finish_exam()


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
        else:
            member = ctx.author
            channel = constants.exam_channel
            self.active_exam = ActiveExam.make(
                draw_manager=self.chairmanmao.draw_manager,
                member=member,
                channel=channel,
                exam=make_exam(),
            )

            await self.active_exam.start()
            # await asyncio.sleep(3)

    @exam.command(name='quit')
    async def cmd_exam_quit(self, ctx):
        constants = self.chairmanmao.constants()
        await ctx.message.add_reaction(constants.dekinai_emoji)
        await self.active_exam.finish_exam()


def make_exam() -> 'Exam':
    questions = []

    import csv
    import random
    with open('data/hsk1.csv') as infile:
        fieldnames = ['question', 'answers', 'unused1', 'unused2']
        reader = csv.DictReader(infile, fieldnames=fieldnames)

        for word in reader:
            questions.append(ExamQuestion(word['question'], word['answers'].split(',')))

    random.shuffle(questions)
    questions = questions[:10]

    return Exam(
        name='HSK 1',
        max_wrong=0,
        questions=questions,
    )


@dataclass
class ActiveExam:
    draw_manager: DrawManager

    member: discord.Member
    channel: discord.TextChannel
    exam: Exam

    exam_start: datetime
    finished: bool
    times_up: bool

    current_question_index: int
    current_question_start: datetime

    answers_given: t.List[str]


    @staticmethod
    def make(draw_manager: DrawManager, member: discord.Member, channel: discord.TextChannel, exam: Exam) -> ActiveExam:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        return ActiveExam(
                draw_manager=draw_manager,
                member=member,
                channel=channel,
                exam=exam,

                exam_start=now,
                finished=False,
                times_up=False,
                current_question_index=-1, # -1 because we need to call next_question() as least once.
                current_question_start=now,
                answers_given=[],
            )

    async def start(self) -> None:
        await self.channel.send(f'Starting exam for {self.member.mention}.')
        await asyncio.sleep(1)
        await self.send_next_question()

    def ready_for_next_question(self) -> bool:
        return len(self.answers_given) == self.current_question_index + 1

    def ready_for_next_answer(self) -> bool:
        return len(self.answers_given) == self.current_question_index

    def current_question(self) -> t.Optional[ExamQuestion]:
        try:
            return self.exam.questions[self.current_question_index]
        except:
            return None

    def next_question(self) -> t.Optional[ExamQuestion]:
        if self.finished:
            return None
        else:
            self.current_question_index += 1
            question = self.exam.questions[self.current_question_index]
            return question

    def is_time_up(self) -> bool:
        now = datetime.now(timezone.utc).replace(microsecond=0)
        duration = now - self.current_question_start
        return duration.total_seconds() > 5

    async def finish_exam(self) -> None:
        self.finished = True

        if self.is_time_up():
            self.times_up = True

        lines = []

        if self.times_up:
            lines.append(f'{self.member.mention}: Time is up')
        else:
            lines.append(f'{self.member.mention}: The exam is complete')

        if not self.times_up:
            questions_answered = self.exam.questions[:len(self.answers_given)]
        else:
            questions_answered = self.exam.questions[:len(self.answers_given) + 1]

        longest_answer = max(len(question.question) for question in questions_answered)

        for question, answer, correct in self.grade():
            emoji = '✅' if correct else '❌'
            correct_answer = question.valid_answers[0]
            question_str = (question.question).ljust(longest_answer + 2, '　')
            answer_str = answer if correct else f'{answer} → {correct_answer}'
            lines.append(f'{emoji} {question_str} {answer_str}')

        if self.times_up:
            emoji = '❌'
            question = self.exam.questions[len(self.answers_given)]
            correct_answer = question.valid_answers[0]
            question_str = (question.question).ljust(longest_answer + 2, '　')
            answer_str = f'*time expired* → {correct_answer}'
            lines.append(f'{emoji} {question_str} {answer_str}')


        await self.channel.send('\n'.join(lines))

    async def answer_question(self, answer: discord.Message) -> None:
        self.answers_given.append(answer.content.strip())

        current_question = self.current_question()
        assert current_question, 'No question was asked'

        content = answer.content.strip()
        correct = content in current_question.valid_answers

        emoji = '✅' if correct else '❌'
        await answer.add_reaction(emoji)

#        if not correct:
#            await self.channel.send('Correct answer: ' + current_question.valid_answers[0])

        # hack to fight timing issues
        self.times_up = False

        if len(self.answers_given) < len(self.exam.questions) and not self.times_up and self.number_wrong() <= self.exam.max_wrong:
            await self.send_next_question()
        else:
            await self.finish_exam()

    async def send_next_question(self) -> None:
        question = self.next_question()
        assert question is not None

        font = 'kuaile'
        image_buffer = self.draw_manager.draw(font, question.question)
        filename = 'hanzi_' + '_'.join('u' + hex(ord(char))[2:] for char in question.question) + '.png'
        file = discord.File(fp=image_buffer, filename=filename)
        await self.channel.send(file=file)

        now = datetime.now(timezone.utc)
        self.current_question_start = now

    def number_wrong(self) -> int:
        num_questions_answered = len(self.answers_given)
        questions = self.exam.questions[:num_questions_answered]

        number_wrong = 0

        for question, answer in zip(questions, self.answers_given):
            if answer not in question.valid_answers:
                number_wrong += 1

        return number_wrong

    def grade(self) -> t.List[t.Tuple[ExamQuestion, Answer, bool]]:
        num_questions_answered = len(self.answers_given)
        questions = self.exam.questions[:num_questions_answered]

        results = []

        for question, answer in zip(questions, self.answers_given):
            correct = answer in question.valid_answers
            results.append((question, answer, correct))

        return results


@dataclass
class Exam:
    name: str
    questions: t.List[ExamQuestion]
    max_wrong: int


@dataclass
class ExamQuestion:
    question: str
    valid_answers: t.List[str]

Answer = str
