import discord
from discord.ext import commands
import asyncio
import youtube_dl
import sqlite3
import aiohttp
import random
import ffmpeg
import datetime  # datetime 모듈 추가

conn = sqlite3.connect('elo_database4.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, elo INTEGER)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS matches (id INTEGER PRIMARY KEY, winner_id INTEGER, loser_id INTEGER, date TEXT)''')
conn.commit()
TIER_EMOJIS = {
    "브론즈": ":bronze_emoji:",
    "실버": ":silver_emoji:",
    "골드": ":gold_emoji:",
    "다이아몬드": ":diamond_emoji:",
    "챔피언": ":champion_emoji:",
}

TIER_urls = {
    "브론즈": "https://media.discordapp.net/attachments/1184419065113092157/1184434458649169960/2Q.png?ex=658bf58c&is=6579808c&hm=267fde8a0257bf8f21c55d05c4343976a8f69d3df1980169cd6583c5dc507b06&=&format=webp&quality=lossless",
    "실버": "https://media.discordapp.net/attachments/1184419065113092157/1184434613960060928/2Q.png?ex=658bf5b1&is=657980b1&hm=f2ebe58a758ad283bb95926e259015c0b71c12834556654cda36bde3a21149f6&=&format=webp&quality=lossless",
    "골드": "https://media.discordapp.net/attachments/1184419065113092157/1184434783028252725/2Q.png?ex=658bf5da&is=657980da&hm=722dc4474fcff677b6b4499929b984ada2717f1af76fab2828329c74caffacf2&=&format=webp&quality=lossless",
    "다이아몬드": "https://media.discordapp.net/attachments/1184419065113092157/1184434876796125225/2Q.png?ex=658bf5f0&is=657980f0&hm=e4d34307acee552494a5c44ac2a02b4d025f034dbbd8f4a8d7d24d75d9b20680&=&format=webp&quality=lossless",
    "챔피언": "https://media.discordapp.net/attachments/1184419065113092157/1184434997218770984/4415916978067.png?ex=658bf60d&is=6579810d&hm=0f32c83759c67a23367a6316e85d219bbbdf3c59d29a31fa30a18f1d9d3cc12e&=&format=webp&quality=lossless&width=838&height=671",
}


def get_tier_emoji(tier):
    # 티어에 따른 이모티콘 반환 로직 추가
    return TIER_EMOJIS.get(tier, ":default_emoji:")
def get_tier_url(tier):
    # 티어에 따른 이모티콘 반환 로직 추가
    return TIER_urls.get(tier, "https://i.namu.wiki/i/C38JeirDm4RFMCvp4d3GO9csIe91B5ERfiuZI40SvIx23IOwPQfPj4aEesXE0W-08IzDm84ktd0v-UDR_6-qgw.webp")
# 나머지 코드 ...
# ...
DEFAULT_ELO = 450
def calculate_tier(elo):
    if elo <= 500:
        return "브론즈"
    elif elo <= 1000:
        return "실버"
    elif elo <= 1400:
        return "골드"
    elif elo <= 1999:
        return "다이아몬드"
    else:
        return "챔피언"

def get_elo(user_id):
    try:
        query = f"SELECT elo FROM users WHERE id = {user_id}"
        print(f"Executing query: {query}")
        cursor.execute(query)
        result = cursor.fetchone()
        if result is not None:
            return result[0]
        else:
            return DEFAULT_ELO
    except Exception as e:
        print(f"Error in get_elo for user ID {user_id}: {e}")
        return DEFAULT_ELO
def update_elo(user_id, new_elo):
    cursor.execute(f"INSERT OR REPLACE INTO users (id, elo) VALUES ({user_id}, {new_elo})")
    conn.commit()


intents = discord.Intents.all()  # 모든 Privileged Gateway Intents 활성화
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.command()
@commands.has_permissions(administrator=True)
async def ELO지급(ctx, member: discord.Member, elo_delta: int):
    if ctx.author.guild_permissions.administrator:
        # 추가된 부분: 관리자 권한 확인
        old_elo = get_elo(member.id)
        new_elo = old_elo + elo_delta
        update_elo(member.id, new_elo)
        await ctx.send(f"{member.mention}의 ELO가 {old_elo}에서 {new_elo}로 지급되었습니다.")
    else:
        await ctx.send("관리자 권한이 필요합니다.")
@bot.event
async def on_member_join(member):
    user_id = member.id
    cursor.execute(f"INSERT OR IGNORE INTO users (id, elo) VALUES ({user_id}, {DEFAULT_ELO})")
    conn.commit()

@bot.command()
async def 초기화(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    if ctx.author.guild_permissions.administrator:
        user_id = member.id

        cursor.execute(f"UPDATE users SET elo = {DEFAULT_ELO} WHERE id = {user_id}")
        cursor.execute(f"DELETE FROM matches WHERE winner_id = {user_id} OR loser_id = {user_id}")
        conn.commit()

        await ctx.send(f"{member.mention}님의 ELO, 승리 횟수, 패배 횟수, 전적이 초기화되었습니다.")
    else:
        await ctx.send("관리자 권한이 필요합니다.")


@bot.command()
async def 정보(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = member.id
    cursor.execute(f"SELECT elo FROM users WHERE id = {user_id}")
    result = cursor.fetchone()

    if result is not None:
        elo = result[0]
        tier = calculate_tier(elo)

        cursor.execute(f"SELECT COUNT(*) FROM matches WHERE winner_id = {user_id}")
        wins = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM matches WHERE loser_id = {user_id}")
        losses = cursor.fetchone()[0]

        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0

        embed = discord.Embed(title=f"{member.display_name}의 정보", color=0x00ff00)
        embed.add_field(name="ELO", value=str(elo), inline=False)
        embed.add_field(name="티어", value=tier, inline=False)
        embed.add_field(name="승리 횟수", value=str(wins), inline=False)
        embed.add_field(name="패배 횟수", value=str(losses), inline=False)
        embed.add_field(name="승률", value=f"{win_rate:.2f}%", inline=False)


        tier_emoji = get_tier_url(tier)
        embed.set_thumbnail(url=tier_emoji)

        await ctx.send(embed=embed)
    else:
        await ctx.send("해당 사용자의 ELO를 찾을 수 없습니다.")


@bot.command()
async def info(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = member.id
    cursor.execute(f"SELECT elo FROM users WHERE id = {user_id}")
    result = cursor.fetchone()

    if result is not None:
        elo = result[0]
        tier = calculate_tier(elo)

        cursor.execute(f"SELECT COUNT(*) FROM matches WHERE winner_id = {user_id}")
        wins = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM matches WHERE loser_id = {user_id}")
        losses = cursor.fetchone()[0]

        win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0

        embed = discord.Embed(title=f"Information for {member.display_name}", color=0x00ff00)
        embed.add_field(name="ELO", value=str(elo), inline=False)
        embed.add_field(name="Tier", value=tier, inline=False)
        embed.add_field(name="Wins", value=str(wins), inline=False)
        embed.add_field(name="Losses", value=str(losses), inline=False)
        embed.add_field(name="Win Rate", value=f"{win_rate:.2f}%", inline=False)


        tier_emoji = get_tier_url(tier)
        embed.set_thumbnail(url=tier_emoji)

        await ctx.send(embed=embed)
    else:
        await ctx.send("해당 사용자의 ELO를 찾을 수 없습니다.")


@bot.command()
@commands.has_permissions(administrator=True)
async def ELO(ctx, winner: discord.Member, loser: discord.Member):
    winner_elo = get_elo(winner.id)
    loser_elo = get_elo(loser.id)

    k_value = 32
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_elo - loser_elo) / 400))

    winner_new_elo = winner_elo + k_value * (1 - expected_winner)
    loser_new_elo = loser_elo + k_value * (0 - expected_loser)

    update_elo(winner.id, round(winner_new_elo))
    update_elo(loser.id, round(loser_new_elo))

    # 추가된 부분: 승리 및 패배 횟수 업데이트
    cursor.execute(f"INSERT INTO matches (winner_id, loser_id, date) VALUES ({winner.id}, {loser.id}, '{datetime.datetime.now()}')")
    conn.commit()

    await ctx.send(f"{winner.mention}이(가) {loser.mention}에게 승리하여 {round(winner_new_elo - winner_elo)}만큼 점수를 획득했습니다.")


@bot.event
async def on_message(message):
    if not message.author.bot:
        user_id = message.author.id

        # Check if the user already exists in the database
        cursor.execute(f"SELECT id FROM users WHERE id = {user_id}")
        existing_user = cursor.fetchone()

        if existing_user is None:
            # If the user is not found, add them to the database with default Elo
            cursor.execute(f"INSERT INTO users (id, elo) VALUES ({user_id}, {DEFAULT_ELO})")
            conn.commit()

    # Process the message as usual
    await bot.process_commands(message)

@bot.command()
async def record(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = member.id
    cursor.execute(
        f"SELECT * FROM matches WHERE winner_id = {user_id} OR loser_id = {user_id} ORDER BY date DESC LIMIT 10")
    matches = cursor.fetchall()

    result = []
    for match in matches:
        winner_name = bot.get_user(match[1]).display_name
        loser_name = bot.get_user(match[2]).display_name
        match_date = datetime.datetime.strptime(match[3], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')

        # Modified section: Display Elo change for each match
        elo_change = round(get_elo(match[1]) - get_elo(match[2]))

        result.append(f"{winner_name} vs {loser_name} ({match_date})  {'Victory' if match[1] == user_id else 'Defeat'} (Elo Change: {elo_change})")

    # Modified section: Use Embed to send the results
    embed = discord.Embed(title=f"Recent Match History for {member.display_name}", color=0x00ff00)

    # If the result is empty, add a message to the Embed stating "No recent match history."
    if not result:
        embed.description = "No recent match history."
    else:
        # If there are results, add them to the Embed
        for match_result in result:
            embed.add_field(name="Match Result", value=match_result, inline=False)

    await ctx.send(embed=embed)
# (이전 코드와 동일한 부분 생략...)
@bot.command()
async def 전적확인(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_id = member.id
    cursor.execute(
        f"SELECT * FROM matches WHERE winner_id = {user_id} OR loser_id = {user_id} ORDER BY date DESC LIMIT 10")
    matches = cursor.fetchall()

    result = []
    for match in matches:
        winner_name = bot.get_user(match[1]).display_name
        loser_name = bot.get_user(match[2]).display_name
        match_date = datetime.datetime.strptime(match[3], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y-%m-%d %H:%M:%S')

        # 수정된 부분: 각 경기에서의 Elo 변동으로 표시
        elo_change = round(get_elo(match[1]) - get_elo(match[2]))

        result.append(f"{winner_name} vs {loser_name} ({match_date})  {'승리' if match[1] == user_id else '패배'}")

    # 수정된 부분: Embed를 사용하여 결과를 보내기
    embed = discord.Embed(title=f"{member.display_name}의 최근 전적", color=0x00ff00)

    # 결과가 비어 있으면 "최근 전적이 없습니다." 메시지를 Embed에 추가
    if not result:
        embed.description = "최근 전적이 없습니다."
    else:
        # 결과가 있으면 Embed에 결과 추가
        for match_result in result:
            embed.add_field(name="결과", value=match_result, inline=False)

    await ctx.send(embed=embed)
import discord
from discord.ext import commands

import discord
from discord.ext import commands


@bot.command()
async def 순위(ctx):
    cursor.execute("SELECT id, elo FROM users ORDER BY elo DESC LIMIT 10")
    leaderboard = cursor.fetchall()

    embed = discord.Embed(title="랭킹", color=discord.Color.gold())

    for i, (user_id, elo) in enumerate(leaderboard):
        user = bot.get_user(user_id)

        # Check if the user is not a bot
        if user and not user.bot:
            user_name = user.display_name
            tier = calculate_tier(elo)
            tier_emoji = get_tier_emoji(tier)
            embed.add_field(name=f"{i + 1}. {user_name}", value=f"**Elo:** {elo}점 {tier_emoji}",
                            inline=False)
        else:
            embed.add_field(name=f"{i + 1}. 비어있음", value=f"", inline=False)

    await ctx.send(embed=embed)
@bot.command()
@commands.has_permissions(administrator=True)
async def 전체초기화(ctx):
    if ctx.author.guild_permissions.administrator:
        # 추가된 부분: 채널에 접속한 모든 멤버의 ELO 초기화
        for member in ctx.channel.members:
            if member.bot:
                continue  # Skip bots

            user_id = member.id
            cursor.execute(f"UPDATE users SET elo = {DEFAULT_ELO} WHERE id = {user_id}")
            cursor.execute(f"DELETE FROM matches WHERE winner_id = {user_id} OR loser_id = {user_id}")

            # 추가된 부분: 새로운 사용자 정보 추가
            cursor.execute(f"INSERT OR IGNORE INTO users (id, elo) VALUES ({user_id}, {DEFAULT_ELO})")

        conn.commit()

        await ctx.send("채널에 접속한 모든 유저의 ELO, 승리 횟수, 패배 횟수, 전적이 초기화되었습니다.")
    else:
        await ctx.send("관리자 권한이 필요합니다.")


@bot.event
async def on_member_join(member):
    if not member.bot:
        user_id = member.id

        # Check if the user already exists in the database
        cursor.execute(f"SELECT id FROM users WHERE id = {user_id}")
        existing_user = cursor.fetchone()

        if existing_user is None:
            # If the user is not found, add them to the database with default Elo
            cursor.execute(f"INSERT INTO users (id, elo) VALUES ({user_id}, {DEFAULT_ELO})")
            conn.commit()
        else:
            # If the user already exists, you can choose to do something else if needed
            pass
@bot.command()
async def leaderboard(ctx):
    cursor.execute("SELECT id, elo FROM users ORDER BY elo DESC LIMIT 10")
    leaderboard = cursor.fetchall()

    result = []
    for i, (user_id, elo) in enumerate(leaderboard):
        user_name = bot.get_user(user_id).display_name
        tier = calculate_tier(elo)
        tier_emoji = get_tier_emoji(tier)
        result.append(f"{i + 1}. {user_name} ({elo}점) {tier_emoji}")

    await ctx.send("\n".join(result))


@bot.command()
async def 도움말(ctx):
    embed = discord.Embed(title="ELO 봇 도움말", color=0x00ff00)
    embed.add_field(name="!초기화 [유저멘션]", value="[유저멘션]의 ELO, 승리 횟수, 패배 횟수, 전적을 초기화합니다. (관리자 권한 필요)", inline=False)
    embed.add_field(name="!정보 [유저멘션]", value="유저의 ELO, 티어, 승리 횟수, 패배 횟수, 승률을 확인합니다.", inline=False)
    embed.add_field(name="!ELO [승자멘션] [패자멘션]", value="Elo 전적을 갱신합니다. (관리자 권한 필요)", inline=False)
    embed.add_field(name="!ELO지급 [멘션] [양]", value="Elo를 줍니다. (관리자 권한 필요)", inline=False)
    embed.add_field(name="!전적확인 [유저멘션]", value="유저의 최근 10경기 전적을 확인합니다.", inline=False)
    embed.add_field(name="!순위", value="ELO 순위를 확인합니다.", inline=False)
    embed.add_field(name="!전체초기화", value="서버의 모든 유저의 ELO, 승리 횟수, 패배 횟수, 전적을 초기화합니다. (관리자 권한 필요)", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def cmd(ctx):
    embed = discord.Embed(title="ELO Bot Help", color=0x00ff00)
    embed.add_field(name="!info [user_mention]", value="Check a user's ELO, tier, wins, losses, and win rate.", inline=False)
    embed.add_field(name="!record [user_mention]", value="View a user's recent match history (last 10 games).", inline=False)
    embed.add_field(name="!leaderboard", value="Check the ELO leaderboard.", inline=False)
    await ctx.send(embed=embed)
@bot.command()
async def cmdjp(ctx):
    embed = discord.Embed(title="ELO Bot ヘルプ", color=0x00ff00)
    embed.add_field(name="!info [ユーザーメンション]", value="ユーザーのELO、ティア、勝利回数、敗北回数、勝率を確認します。", inline=False)
    embed.add_field(name="!record [ユーザーメンション]", value="ユーザーの最近の対戦履歴（最後の10試合）を表示します。", inline=False)
    embed.add_field(name="!leaderboard", value="ELOリーダーボードを確認します。", inline=False)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f'{bot.user} 로그인 성공')
    await bot.change_presence(activity=discord.Game(name='/도움말,/cmd(ENG),/cmdjp(JP)'))
bot_token = "MTEzMzY3MTQ5Njk2ODA1NjgzMg.GEE4r0.6V2KyRVmrxcSi-DA2OMsB4BQgphF2iUxB5rNeg"
bot.run(bot_token)