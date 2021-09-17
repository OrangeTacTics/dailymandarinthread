from __future__ import annotations
import typing as t
import os
from dataclasses import dataclass
from chairmanmao.types import UserId, Json

import httpx

import discord
from discord.ext import commands
from chairmanmao.cogs import ChairmanMaoCog


class LearnersCog(ChairmanMaoCog):
    @commands.Cog.listener()
    async def on_ready(self):
        self.chairmanmao.logger.info('LearnersCog')

    @commands.Cog.listener()
    async def on_message(self, message):
        MEMBER_ID_KOTOBA = int(os.getenv('MEMBER_ID_KOTOBA', ''))
        if message.author.bot and message.author.id == MEMBER_ID_KOTOBA:
            await handle_kotoba(self.chairmanmao.api, message)

    @commands.command(name='learner', help='Add or remove 中文学习者 role.')
    @commands.has_role('同志')
    async def cmd_learner(self, ctx, flag: bool = True):
        learner_role = discord.utils.get(ctx.guild.roles, name="中文学习者")

        self.chairmanmao.api.as_comrade(ctx.author.id).set_learner(flag)
        self.chairmanmao.queue_member_update(ctx.author.id)
        if flag:
            await ctx.send(f'{ctx.author.display_name} has been added to {learner_role.name}')
        else:
            await ctx.send(f'{ctx.author.display_name} has been removed from {learner_role.name}')

    @commands.command(name='hsk', help='See your HSK rank.')
    @commands.has_role('同志')
    async def cmd_hsk(self, ctx, member: commands.MemberConverter = None):
        if member is not None:
            target_member = member
        else:
            target_member = ctx.author

        target_username = self.chairmanmao.member_to_username(target_member)
        hsk_level = self.chairmanmao.api.as_chairman().get_hsk(target_member.id)

        if hsk_level is None:
            await ctx.send(f'{target_username} is unranked.')
        else:
            await ctx.send(f'{target_username} has reached HSK {hsk_level}.')

    @commands.command(name='test')
    @commands.has_role("中文学习者")
    async def cmd_test(self, ctx):
        hsk_level = self.chairmanmao.api.as_chairman().get_hsk(ctx.author.id)

        if hsk_level is None:
            aiming_for = 1
        else:
            aiming_for = hsk_level + 1

        if aiming_for > 2:
            # msg = 'You are at the max HSK level.'
            msg = 'Currently, only HSK 1 and 2 tests are available.'
        else:
            num_questions = SCORE_LIMIT_BY_DECK.get(f'dmt_hsk{aiming_for}')
            msg = f'For the next test, use this command in the #🏫考试 channel:\n`k!quiz dmt_hsk{aiming_for} nodelay mmq=1 atl=10 {num_questions}`'

        await ctx.send(msg)


@dataclass
class QuizResults:
    user_id: UserId
    deck_name: str
    quiz_id: str


async def get_quiz_results(api, message: discord.Message) -> t.Optional[QuizResults]:
    fields = {}

    for embed in message.embeds:
        for field in embed.fields:
            fields[field.name] = field.value

    if 'Final Scores' in fields:
        final_score = fields['Final Scores']
        assert final_score.startswith('<@')
        assert '>' in final_score
        idx = final_score.index('>')
        user_id = int(final_score[2:idx])

        game_report = fields['Game Report']
        quiz_id = re.search(r'game_reports/([a-f0-9]+)\)', game_report).group(1)  # type: ignore

        url = f"https://kotobaweb.com/api/game_reports/{quiz_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            kotoba_json = response.json()

        if len(kotoba_json['decks']) != 1:
            return None

        deck = kotoba_json['decks'][0]

        deck_unique_id = deck['uniqueId']
        deck_start_index = deck.get('startIndex')
        deck_end_index = deck.get('endIndex')
        deck_mc = deck['mc']

        allowed_decks = {
            'd4bc0da0-8835-467c-a2c2-5d1d3991ae0f': 'dmt_hsk1',
            'c102f308-3f1e-44cd-a15d-803de4f16d08': 'dmt_hsk2',
#            '': 'dmt_hsk3',
#            '': 'dmt_hsk4',
#            '': 'dmt_hsk5',
#            '': 'dmt_hsk6',
        }

        deck_name = allowed_decks.get(deck_unique_id)
        if deck_name is None:
            return None

        settings_json = kotoba_json['settings']
        if not allowable_settings(deck_name, settings_json):
            return None

        is_loaded = kotoba_json['isLoaded']

        assert is_loaded is False
        assert len(kotoba_json['participants']) == 1
        assert kotoba_json['participants'][0]['discordUser']['id'] == str(user_id)
        assert len(kotoba_json['scores']) == 1

        assert deck_start_index is None
        assert deck_end_index is None
        assert deck_mc is False

        question_count = len(kotoba_json['questions'])
        score = kotoba_json['scores'][0]['score']

        if score == question_count:
            hsk_level = int(deck_name[-1])

            old_hsk_level = api.as_chairman().get_hsk(user_id)

            if old_hsk_level is None or old_hsk_level < hsk_level:
                api.as_chairman().set_hsk(user_id, hsk_level)

                return QuizResults(
                    user_id=user_id,
                    deck_name=deck_name,
                    quiz_id=quiz_id
                )

            else:
                return None
        else:
            return None

    else:
        return None


SCORE_LIMIT_BY_DECK = {
    'dmt_hsk1': 10,
    'dmt_hsk2': 15,
    'dmt_hsk3': 20,
    'dmt_hsk4': 20,
    'dmt_hsk5': 25,
    'dmt_hsk6': 30,
}


def allowable_settings(deck_name: str, settings_json: Json) -> bool:
    required_settings = {
        'shuffle': True,
        'scoreLimit': SCORE_LIMIT_BY_DECK[deck_name],
        'maxMissedQuestions': 1,
        'answerTimeLimitInMs': 10000,
#        "fontSize": 80,
        "fontColor": "rgb(0, 0, 0)",
        "backgroundColor": "rgb(255, 255, 255)",
        "font": "Noto Sans CJK",
    }

    for setting_name, required_value in required_settings.items():
        actual_value = settings_json[setting_name]
        if actual_value != required_value:
            print('bad setting:', setting_name, 'has value', actual_value, 'but needs to be', required_value)
            return False

    return True


async def handle_kotoba(api, message):
    quiz_results = await get_quiz_results(api, message)
    if quiz_results is not None:

        profile = api.as_chairman().get_profile(quiz_results.user_id)
        await message.channel.send(f'{profile.discord_username} has passed the {quiz_results.deck_name} quiz.')
        chairmanmao.queue_member_update(profile.id)
