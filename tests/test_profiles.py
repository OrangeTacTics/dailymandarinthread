import os

from dotenv import load_dotenv
import pytest


@pytest.mark.asyncio
async def test_create(empty_db, api):
    assert len(await api.leaderboard()) == 0
    await api.register(
        user_id=182370676877819904,
        discord_username='OrangeTacTics#0949',
    )
    assert len(await api.leaderboard()) == 1


@pytest.mark.asyncio
async def test_leaderboard(three_user_db, api):
    assert len(await api.leaderboard()) == 3


@pytest.mark.asyncio
async def test_starting_social_credit(empty_db, api):
    mao_user_id = 888950825970462730

    await api.register(
        user_id=mao_user_id,
        discord_username='ChairmanMao#7877',
    )
    assert await api.social_credit(mao_user_id) == 1000


@pytest.mark.asyncio
async def test_starting_yuan(empty_db, api):
    mao_user_id = 888950825970462730
    tactics_user_id = 182370676877819904

    await api.register(
        user_id=tactics_user_id,
        discord_username='OrangeTacTics#0949',
    )
    assert await api.yuan(tactics_user_id) == 0

    await api.register(
        user_id=mao_user_id,
        discord_username='ChairmanMao#7877',
    )
    assert await api.yuan(mao_user_id) == 10000


@pytest.mark.asyncio
async def test_transfer_yuan(three_user_db, api):
    mao_user_id = 888950825970462730
    tactics_user_id = 182370676877819904

    assert await api.yuan(mao_user_id) == 10000
    assert await api.yuan(tactics_user_id) == 0

    await api.transfer(mao_user_id, tactics_user_id, 10)
    assert await api.yuan(mao_user_id) == 9990
    assert await api.yuan(tactics_user_id) == 10


@pytest.mark.asyncio
async def test_honor_dishonor(three_user_db, api):
    user_id = 182370676877819904
    assert await api.social_credit(user_id) == 1000
    await api.honor(user_id, 10)
    assert await api.social_credit(user_id) == 1010
    await api.dishonor(user_id, 15)
    assert await api.social_credit(user_id) == 995


@pytest.mark.asyncio
async def test_mine(three_user_db, api):
    tactics_user_id = 182370676877819904
    await api.mine(tactics_user_id, '猫')
    assert await api.get_mined(tactics_user_id) == ['猫']
    await api.mine(tactics_user_id, '狗')
    assert await api.get_mined(tactics_user_id) == sorted(['猫', '狗'])


@pytest.mark.asyncio
async def test_name(three_user_db, api):
    tactics_user_id = 182370676877819904
    assert await api.get_name(tactics_user_id) == 'OrangeTacTics'
    await api.set_name(tactics_user_id, 'Tac')
    assert await api.get_name(tactics_user_id) == 'Tac'


@pytest.mark.asyncio
async def test_leaderboard(three_user_db, api):
    mao_user_id = 888950825970462730
    tactics_user_id = 182370676877819904
    snickers_user_id = 878851905021947924

    await api.honor(mao_user_id, 1)
    await api.dishonor(snickers_user_id, 1)

    leaderboard = await api.leaderboard()
    assert leaderboard[0].display_name == 'ChairmanMao'
    assert leaderboard[1].display_name == 'OrangeTacTics'
    assert leaderboard[2].display_name == 'Snickers'
