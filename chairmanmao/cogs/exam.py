from __future__ import annotations
import typing as t
from dataclasses import dataclass
import random

import discord
from discord.ext import commands, tasks

from chairmanmao.cogs import ChairmanMaoCog
from chairmanmao.types import Exam
from chairmanmao.exam import Examiner, TickResult
from chairmanmao.exam import (
    Timeout,
    Correct,
    Incorrect,
)


class ExamCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info("ExamCog")
        self.loop.start()
        self.active_exam: t.Optional[ActiveExam] = None

    @commands.Cog.listener()
    async def on_message(self, message):
        if self.active_exam:
            active_exam = self.active_exam
            if message.channel.id == active_exam.channel.id and message.author.id == active_exam.member.id:
                if not message.content.startswith("!") and active_exam.examiner.ready_for_next_answer():
                    await self.send_answer(active_exam, message)

    @tasks.loop(seconds=1)
    async def loop(self):
        if self.active_exam is not None:
            tick_result = self.active_exam.examiner.tick()

            if tick_result == TickResult.next_question:
                await self.send_next_question(self.active_exam)
            elif tick_result == TickResult.finished:
                await self.show_results(self.active_exam)
                await self.mine_correct_answers(self.active_exam)
                await self.reward(self.active_exam)
                self.active_exam = None
            elif tick_result == TickResult.timeout:
                await self.reply_to_answer(self.active_exam)
            elif tick_result == TickResult.nothing:
                pass
            elif tick_result == TickResult.pause:
                pass

    @commands.group()
    async def exam(self, ctx):
        constants = self.chairmanmao.constants()
        if ctx.invoked_subcommand is None:
            exam_name = await self.next_exam_for(ctx.author)
            if exam_name is None:
                await ctx.send("Available exams: " + " ".join(await self.exam_names()))
                return

            if exam_name is not None:
                lines = [
                    f"The next exam you are scheduled to take is {exam_name}.",
                ]

                if ctx.channel.id == constants.exam_channel.id:
                    lines.append(f"To take the exam, use `!exam start`")
                else:
                    lines.append(f"To take the exam, go to {constants.exam_channel.mention} and use `!exam start`")

                await ctx.send("\n".join(lines))

            else:
                await ctx.send(f"There are currently no exams ready for you.")

    @exam.command(name="card")
    @commands.has_role("共产党员")
    async def cmd_card(self, ctx, exam_name: str, question: str):
        exam = await self.chairmanmao.api.exam(exam_name)
        question = [q for q in exam.deck if q.question == question][0]
        await ctx.send(f"Question: {question}")

    @exam.command(name="edit")
    @commands.has_role("共产党员")
    async def cmd_edit(self, ctx, exam_name: str, question: str, *, valid_answers_str: str):
        exam = await self.chairmanmao.api.exam(exam_name)
        old_card = [q for q in exam.deck if q.question == question][0]

        await self.chairmanmao.api.edit_exam_answers(
            exam_name,
            question,
            new_valid_answers=[a.strip() for a in valid_answers_str.split(",")],
        )

        exam = await self.chairmanmao.api.exam(exam_name)
        new_card = [q for q in exam.deck if q.question == question][0]
        await ctx.send(f"Card has been updated:\nOLD: {old_card}\nNEW: {new_card}")

    @exam.command(name="list")
    async def cmd_exam_list(self, ctx):
        await ctx.send("Available exams: " + " ".join(await self.exam_names()))

    @exam.command(name="start")
    async def cmd_exam_start(self, ctx, _exam_name: t.Optional[str] = None):
        if _exam_name is not None:
            description = "\n".join(
                [
                    "You may run an exam with `!exam start`",
                    "There is no need to specify the exam name.",
                ]
            )
            embed = discord.Embed(
                title="Note",
                description=description,
                color=0xFF0000,
            )
            await ctx.channel.send(embed=embed)

        exam_name = await self.next_exam_for(ctx.author)
        if exam_name is not None:
            exam: t.Optional[Exam] = await self.chairmanmao.api.exam(exam_name)
        else:
            exam = None

        if exam is None:
            await ctx.send("There is currently no exam for you.")
            return

        constants = self.chairmanmao.constants()
        if ctx.channel.id != constants.exam_channel.id:
            await ctx.send(f"This command must be run in {constants.exam_channel.mention}")
            return

        if self.active_exam is not None:
            await ctx.send(f"{self.active_exam.member.mention} is currently taking an exam")
            return

        active_exam = self.create_active_exam(ctx.author, ctx.channel, exam)
        self.active_exam = active_exam
        await self.send_exam_start_embed(active_exam)

    @exam.command(name="practice")
    async def cmd_exam_practice(self, ctx, exam_name: t.Optional[str] = None):
        if exam_name is None:
            exam_name = await self.next_exam_for(ctx.author)
            if exam_name is None:
                await ctx.send("Available exams: " + " ".join(await self.exam_names()))
                return

        exam: t.Optional[Exam] = await self.chairmanmao.api.exam(exam_name)

        if exam is None:
            await ctx.send("Available exams: " + " ".join(await self.exam_names()))
            return

        constants = self.chairmanmao.constants()
        if ctx.channel.id != constants.exam_channel.id:
            await ctx.send(f"This command must be run in {constants.exam_channel.mention}")
            return

        if self.active_exam is not None:
            await ctx.send(f"{self.active_exam.member.mention} is currently taking an exam")
            return

        active_exam = self.create_active_exam(ctx.author, ctx.channel, exam, practice=True)
        self.active_exam = active_exam
        await self.run_exam(active_exam)

    @exam.command(name="quit")
    async def cmd_exam_quit(self, ctx):
        constants = self.chairmanmao.constants()
        if ctx.channel.id != constants.exam_channel.id:
            await ctx.send(f"This command must be run in {constants.exam_channel.mention}")
            return

        if self.active_exam is None:
            #            await ctx.send(f'There is no exam in progress.')
            return

        if self.active_exam.member.id != ctx.author.id:
            #            await ctx.send(f"The exam in progress isn't yours")
            return

        self.active_exam.examiner.give_up()
        await self.reply_to_answer(self.active_exam)

    async def next_exam_for(self, member: discord.Member) -> t.Optional[str]:
        current_hsk = await self.chairmanmao.api.get_hsk(member.id)
        if current_hsk is None:
            return "hsk1"
        else:
            if current_hsk < 6:
                return f"hsk{current_hsk+1}"
            else:
                return None

    async def exam_names(self) -> t.List[str]:
        return sorted(await self.chairmanmao.api.get_exam_names())

    def create_active_exam(
        self,
        member: discord.Member,
        channel: discord.TextChannel,
        exam: Exam,
        practice: bool = False,
    ) -> ActiveExam:
        return ActiveExam.make(
            member=member,
            channel=channel,
            exam=exam,
            practice=practice,
        )

    async def reply_to_answer(self, active_exam: ActiveExam) -> None:
        answer = active_exam.examiner.previous_answer()
        constants = self.chairmanmao.constants()
        question = active_exam.examiner.current_question()

        if isinstance(answer, Correct):
            emoji = "✅"
            color = 0x00FF00
            correct_answer = f"{question.valid_answers[0]}"
        elif isinstance(answer, Incorrect):
            emoji = "❌"
            color = 0xFF0000
            correct_answer = f"{question.valid_answers[0]}"
        elif isinstance(answer, Timeout):
            emoji = "⏲️"
            color = 0xD0DEEC
            correct_answer = f"{question.valid_answers[0]}"
        else:  # isinstance(answer, Quit):
            emoji = constants.dekinai_emoji
            color = 0xFFDBAC
            correct_answer = f"{question.valid_answers[0]}"

        description = f"{emoji}　{question.question}　　{correct_answer}　　*{question.meaning}*"

        embed = discord.Embed(
            description=description,
            color=color,
        )
        await active_exam.channel.send(embed=embed)

    async def send_exam_start_embed(self, active_exam: ActiveExam) -> None:
        exam = active_exam.exam

        embed = discord.Embed(
            color=0xFFA500,
        )

        embed.set_author(
            name=active_exam.member.display_name,
            icon_url=active_exam.member.avatar_url,
        )
        embed.add_field(
            name="Deck",
            value=exam.name,
            inline=True,
        )

        embed.add_field(
            name="Questions",
            value=f"{exam.num_questions}",
            inline=True,
        )

        embed.add_field(
            name="Time Limit",
            value=f"{active_exam.examiner.timelimit} seconds",
            inline=False,
        )
        if active_exam.examiner.max_wrong is not None:
            embed.add_field(
                name="Mistakes Allowed",
                value=f"{active_exam.examiner.max_wrong}",
                inline=True,
            )

        await active_exam.channel.send(embed=embed)

    async def send_answer(
        self,
        active_exam: ActiveExam,
        message: discord.Message,
    ) -> None:
        answer = message.content.strip()
        active_exam.examiner.answer(answer)
        await self.reply_to_answer(active_exam)

    async def send_next_question(self, active_exam: ActiveExam) -> None:
        question = active_exam.examiner.current_question()

        font = "kuaile"
        size = 64
        color = (255, 0, 0)
        image_buffer = self.chairmanmao.draw_manager.draw(
            font,
            question.question,
            size=size,
            color=color,
        )
        filename = "hanzi_" + "_".join("u" + hex(ord(char))[2:] for char in question.question) + ".png"
        file = discord.File(fp=image_buffer, filename=filename)
        await active_exam.channel.send(file=file)
        self.chairmanmao.logger.info(f"{question.question}　　{question.valid_answers[0]}")

    async def show_results(self, active_exam: ActiveExam) -> None:
        lines = []

        # if is not practice
        if not active_exam.examiner.fail_on_timeout:
            questions_answered = active_exam.examiner.questions[: len(active_exam.examiner.answers_given)]
            longest_answer = max(len(question.question) for question in questions_answered)

            for question, answer in active_exam.examiner.grade():
                correct = isinstance(answer, Correct)
                emoji = "✅" if correct else "❌"
                correct_answer = question.valid_answers[0]
                question_str = (question.question).ljust(longest_answer + 2, "　")
                answer_str = answer if correct else f"{answer} → {correct_answer}"
                lines.append(f"{emoji}　{question_str} {answer_str}　*{question.meaning}*")

            if active_exam.examiner.passed():
                title = "ActiveExam Passed: " + active_exam.exam.name
                color = 0x00FF00
            else:
                title = "ActiveExam Failed: " + active_exam.exam.name
                color = 0xFF0000

            embed = discord.Embed(
                title=title,
                description="\n".join(lines),
                color=color,
            )
            embed.set_author(
                name=active_exam.member.display_name,
                icon_url=active_exam.member.avatar_url,
            )
            if (
                active_exam.examiner.passed()
                and active_exam.examiner.max_wrong is not None
                and active_exam.examiner.max_wrong > 0
            ):
                score = active_exam.examiner.score() * 100
                embed.add_field(name="Score", value=f"{score:2.1f}%", inline=True)

        # if is practice
        else:
            questions_answered = active_exam.examiner.questions[: len(active_exam.examiner.answers_given)]
            longest_answer = max(len(question.question) for question in questions_answered)

            title = "ActiveExam Practice: " + active_exam.exam.name
            color = 0x00FF00

            sampled_corrections = [(q, a) for (q, a) in active_exam.examiner.grade() if isinstance(a, Incorrect)]
            while len(sampled_corrections) > 5:
                sampled_corrections.pop(random.randrange(len(sampled_corrections)))

            for question, answer in sampled_corrections:
                correct = isinstance(answer, Correct)
                emoji = "✅" if correct else "❌"
                correct_answer = question.valid_answers[0]
                question_str = (question.question).ljust(longest_answer + 2, "　")
                answer_str = answer if correct else f"{answer} → {correct_answer}"
                lines.append(f"{emoji}　{question_str} {answer_str}　*{question.meaning}*")

            embed = discord.Embed(
                title=title,
                description="\n".join(lines),
                color=color,
            )
            embed.set_author(
                name=active_exam.member.display_name,
                icon_url=active_exam.member.avatar_url,
            )
            score = active_exam.examiner.score() * 100
            embed.add_field(name="Score", value=f"{score:2.1f}%", inline=True)

        await active_exam.channel.send(embed=embed)

    async def mine_correct_answers(self, active_exam: ActiveExam) -> None:
        for question, answer in active_exam.examiner.grade():

            if isinstance(answer, Correct):
                await self.chairmanmao.api.mine(active_exam.member.id, question.question)

    async def reward(self, active_exam: ActiveExam) -> None:
        if active_exam.examiner.practice:
            return

        current_hsk = await self.chairmanmao.api.get_hsk(active_exam.member.id)
        if current_hsk is not None and current_hsk >= active_exam.exam.hsk_level:
            return

        if active_exam.examiner.passed():
            username = self.chairmanmao.member_to_username(active_exam.member)

            await self.chairmanmao.api.set_learner(active_exam.member.id, True)
            await self.chairmanmao.api.set_hsk(active_exam.member.id, active_exam.exam.hsk_level)
            self.chairmanmao.queue_member_update(active_exam.member.id)
            self.chairmanmao.logger.info(f"User {username} passed HSK {active_exam.exam.hsk_level}.")
            constants = self.chairmanmao.constants()
            await constants.commentators_channel.send(f"{username} passed the HSK {active_exam.exam.hsk_level} exam.")


@dataclass
class ActiveExam:
    examiner: Examiner
    exam: Exam
    channel: discord.Channel
    member: discord.Member

    @staticmethod
    def make(
        member: discord.Member,
        channel: discord.TextChannel,
        exam: Exam,
        practice: bool = False,
    ) -> ActiveExam:
        examiner = Examiner.make(
            exam=exam,
            practice=practice,
        )

        return ActiveExam(
            examiner=examiner,
            exam=exam,
            member=member,
            channel=channel,
        )
