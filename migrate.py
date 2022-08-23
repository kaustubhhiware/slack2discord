#!/usr/bin/env python3
from collections import OrderedDict
from datetime import datetime
import io
from html import unescape
import json
import re
import shortuuid
import string
import time
import textwrap
import os

import aiohttp
import discord
from discord.ext import commands

# limit is 10,000 messages per 10 minutes
# change this according to your slack workspace total messages
THROTTLE_TIME_SECONDS = 0.3
FILE_DOWNLOAD_TIMEOUT_SECONDS = 60
TOKEN_VAR = "S2DTOKEN"
BOT_PREFIX = "s2d!"
# discord's message char limit is 2000
# assuming 200 chars sufficient for name + date
TEXT_LIMIT = 2000 - 200
THREAD_NAME_LEN = 20
# files above this size are not uploaded
# this is to forego any issues with discord client when adding files.
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

class Message:
    def __init__(self, timestr, text, username):
        self.timestr = timestr
        self.text = text
        self.username = username

    def __repr__(self):
        return f"**{self.username}** *{self.timestr}*\n{self.text}"


class SlackFile:
    def __init__(self, title, url):
        self.title = title
        self.url = url


class Thread:
    def __init__(self, timestamp, texts, username, replyTimes, emojis, files):
        self.timestamp = timestamp # mostly for debugging
        self.messages = list()
        for text in texts:
            self.messages.append(Message(timestamp, text, username))
        self.replyTimes = replyTimes
        self.isReply = False
        self.emojis = emojis # list of emojis
        self.files = files # list of SlackFiles

    def __repr__(self):
        return repr(self.messages)

    def markAsReply(self):
        # this means don't print this message, add it in some thread
        self.isReply = True


def format_text(msg, users, channels):
    '''
    add channel, user references. Format links, and encoded html
    '''
    for user_id, name in users.items():
        msg = msg.replace(f"<@{user_id}>", f"@{name}")
    for channel_id, name in channels.items():
        msg = msg.replace(f"<#{channel_id}>", f"#{name}")

    # format links, punctuation marks
    msg = re.sub(r"<(.+)\|(.+)>", "[\\2](\\1)", unescape(msg))
    return msg


def build_msg_dir(fpaths, users, channels):
    '''
    returned object is a dict of timestamp to Thread object
        timestamp (float)
        Message
        replies - List of timestamps
        isReply - is it a reply or a message in the channel
        emojis
        files - list of file urls
    '''
    msg_dir = dict()

    for file in fpaths:
        try:
            with open(file, encoding="utf-8") as f:
                for message in json.load(f):
                    msg_check = all(key in message for key in ['ts', 'text', 'user_profile'])
                    file_check = all(key in message for key in ['ts', 'text', 'files'])
                    if not msg_check and not file_check :
                        print(f"[WARNING] username, timestamp, or text/file missing")
                        continue

                    # Apr 10, 2020 at 04:45 AM
                    ts_str = datetime.fromtimestamp(float(message['ts'])).strftime('%b %d, %Y at %I:%M %p')
                    username = "user_not_found" # file upload
                    if 'user_profile' in message:
                        username = message['user_profile']['display_name'] or message['user_profile']['real_name']
                    elif message['user'] in users:
                        username = users[message['user']]
                    # discord's message char limit is 4K, but slack's is 40K
                    # Break it down to smaller chunks
                    # set an empty message, to be used for editing when file in thread
                    texts = ["<empty>"]
                    if 'text' in message and len(message['text']) != 0:
                        # respect \n in message
                        texts = textwrap.wrap(message['text'], TEXT_LIMIT,
                                    break_long_words=False, replace_whitespace=False, drop_whitespace=False,
                                )
                        texts = [format_text(txt, users, channels) for txt in texts]

                    emojis = list()
                    # does not export emoji count - kinda obvious if you think about it.
                    if 'reactions' in message:
                        for reaction in message['reactions']:
                            emojis.append(reaction['name'])

                    files = list() # list of slackFiles
                    if 'files' in message:
                        for slackfile in message['files']:
                            fname = slackfile['title'] if 'title' in slackfile else slackfile['name']
                            # ensure text files render correctly
                            files.append(SlackFile(fname, slackfile['url_private_download']))

                    # add reply timestamps to the threads
                    replies = list()
                    if 'replies' in message:
                        # It is ok to sort it right here because different channels
                        # will have non-intersecting threads, and your exported slack
                        # messages always keep track of all replies inside.
                        replies = [float(reply['ts']) for reply in message['replies']]
                        replies.sort()

                    msg_dir[float(message['ts'])] = Thread(ts_str, texts, username, replies, emojis, files)
        except Exception as e:
            print(f"[ERROR] {e}")


    # mark messages as thread starters or thread messages
    for timestamp in msg_dir:
        for reply in msg_dir[timestamp].replyTimes:
            if reply in msg_dir:
                msg_dir[reply].markAsReply()

    return OrderedDict(sorted(msg_dir.items()))


def get_users(dir):
    '''
    Map user id to user name
    '''
    userfile = os.path.join(dir, 'users.json')
    if not os.path.exists(userfile):
        return None

    userMap = dict() # map of user id to display name
    try:
        with open(userfile, encoding="utf-8") as f:
            users = json.load(f)
            for user in users:
                username = user['profile']['display_name'] if 'display_name' in user['profile'] else user['profile']['real_name']
                userMap[user['id']] = username
    except Exception as e:
        return None

    return userMap


def get_channels(dir):
    '''
    Map channel id to channel name
    '''
    channelfile = os.path.join(dir, 'channels.json')
    if not os.path.exists(channelfile):
        return None

    channelMap = dict() # map of channel id to name
    try:
        with open(channelfile, encoding="utf-8") as f:
            channels = json.load(f)
            for channel in channels:
                channelMap[channel['id']] = channel['name']
    except Exception as e:
        return None

    return channelMap


def get_pinned_messages(dir, channelNames):
    '''
    Get pinned messages for a few channels
    '''
    channelfile = os.path.join(dir, 'channels.json')
    if not os.path.exists(channelfile):
        return None

    pinned = dict()
    try:
        with open(channelfile, encoding="utf-8") as f:
            channels = json.load(f)
            for channel in channels:
                if channel['name'] not in channelNames:
                    continue
                for pin in channel['pins']:
                    pinned[float(pin['id'])] = True
    except Exception as e:
        return None

    return pinned


def get_filepaths(dir, channelNames):
    '''
    Sends a list of json files in specified exported channels
    '''
    fpaths = list()

    for channel in channelNames:
        channelDir = os.path.join(dir, channel)
        if not os.path.exists(channelDir) or not os.path.isdir(channelDir):
            # redundant check
            print(f"{channel} channel directory doesn't exist!")
            continue
        
        for f in os.listdir(channelDir):
            if not f.endswith('.json'):
                continue
            fpaths.append(os.path.join(channelDir, f))

    return fpaths


async def d_pin_message(dMessage, ts, pinned_messages):
    '''
    pins a message if it should be
    '''
    if pinned_messages is None or ts not in pinned_messages:
        return
    try:
        await dMessage.pin()
    except Exception as pe:
        print(f"[ERROR] Pinnning message - {pe}")


async def d_add_emojis(dMessage, emojis):
    '''
    Adds multiple emojis to a message
    Not called anywhere, doesn't work as intended yet.
    '''
    if emojis is None:
        return
    for emoji  in emojis:
        try:
            # ToDo: convert str emoji :x: to emoji ❌
            await dMessage.add_reaction(f":{emoji}:")
        except Exception as ee:
            print(f"[ERROR] Adding emoji {emoji} - {ee}")


async def d_add_files(dMessage, files):
    '''
    Add files to messages

    If any file download takes longer than a minute, imma drop it.
    '''
    if files is None:
        return
    timeout = aiohttp.ClientTimeout(total=FILE_DOWNLOAD_TIMEOUT_SECONDS)

    dFiles = list()
    for slackFile in files:
        async with aiohttp.ClientSession() as session:
            async with session.get(slackFile.url, timeout = timeout) as resp:
                if resp.status != 200:
                    print(f"[WARNING] Could not download file {slackFile.title}")
                    await dMessage.edit(content=dMessage.content + "\n[slack2discord] file download failed")
                    continue
                if resp.content_length is not None and resp.content_length > MAX_FILE_SIZE_BYTES:
                    print(f"[WARNING] File too big! Not sending to discord - {slackFile.title}")
                    await dMessage.edit(content=dMessage.content + "\n[slack2discord] file too big")
                    continue

                data = io.BytesIO(await resp.read())
                dFiles.append(discord.File(data, slackFile.title))

    try:
        await dMessage.edit(attachments=dFiles)
    except Exception as fe:
        await dMessage.edit(content=dMessage.content + "\n[slack2discord] file upload failed")
        print(f"[WARNING] Could not upload files - {fe}")


def register_commands():
    @bot.command(pass_context=True)
    async def hi(ctx):
        '''
        Check that this bot works - a simple acknowledgement.
        '''
        await ctx.send("Hello there!")


    @bot.command(pass_context=True)
    async def migrate(ctx, *pathArg):
        '''
        Import exported slack channels from the export directory to the discord channel it's invoked in.
        Usage: `s2d!migrate exported_dir slack_ch1 slack_ch2`
        :param dir:
        :param channels:
        
        A strong assumption is that there are no two messages in the same timestamp (including two decimals)
        '''
        dir = list(pathArg)[0]
        if not os.path.exists(dir):
            await ctx.send(f"Directory {dir} does not exist! Use a valid path.")
            return

        channelNames = list(pathArg)[1:]
        invalid_channels = list()
        # if any channel does not exist, throw an error and do nothing
        for channel in channelNames:
            channelDir = os.path.join(dir, channel)
            if not os.path.exists(channelDir) or not os.path.isdir(channelDir):
                invalid_channels.append(channel)

        if len(invalid_channels) != 0:
            await ctx.send(f"The following channels do not exist: {', '.join(invalid_channels)}")
            await ctx.send("Ensure all channels provided")
            return

        # create lists - users, channels and valid files
        users = get_users(dir)
        if not users:
            await ctx.send(f"Users don't seem right. Check users.json in your directory")
            return

        channels = get_channels(dir)
        if not channels:
            await ctx.send(f"Channels don't seem right. Check channels.json in your directory")
            return

        filepaths = get_filepaths(dir, channelNames)
        if not filepaths:
            await ctx.send(f"There aren't any valid files in the channels you mentioned.")
            return

        # create map of timestamps that are pinned in this channel, if so pin them on addition.
        pinned_messages = get_pinned_messages(dir, channelNames)

        # build a list of threads, build later
        msg_dir = build_msg_dir(filepaths, users, channels)
        for ts in msg_dir:
            print(f"moving message at {ts}")
            if msg_dir[ts].isReply:
                # replies will be printed in parent thread
                continue
            
            # if the message is very long, only the last message is pinned.
            # This also creates a thread at the very last message.
            dMessage = discord.Message
            for message in msg_dir[ts].messages:
                dMessage = await ctx.send(message)
            await d_pin_message(dMessage, ts, pinned_messages)
            # await d_add_emojis(dMessage, msg_dir[ts].emojis)
            await d_add_files(dMessage, msg_dir[ts].files)
            time.sleep(THROTTLE_TIME_SECONDS)

            if len(msg_dir[ts].replyTimes) > 0:
                # it's possible the message is empty (image), so make a random thread name
                thread_name = shortuuid.ShortUUID().random(length=THREAD_NAME_LEN)
                # check if thread name is possible
                if len(msg_dir[ts].messages) > 0:
                    thread_name = msg_dir[ts].messages[0]
                    # take first 20 chars after omitting punctuation
                    thread_name = str(thread_name).translate(str.maketrans('', '', string.punctuation))[:THREAD_NAME_LEN]

                # create a thread, use it immediately
                dThread = await dMessage.create_thread(name=thread_name)
                for replyTime in msg_dir[ts].replyTimes:
                    print(f"\tmoving reply at {replyTime}")
                    # if for some reason, a reply is not present in messages
                    if replyTime not in msg_dir:
                        continue

                    dThreadMsg = discord.Message
                    for message in msg_dir[replyTime].messages:
                        dThreadMsg = await dThread.send(message)
                    await d_pin_message(dThreadMsg, replyTime, pinned_messages)
                    # await d_add_emojis(dThreadMsg, msg_dir[replyTime].emojis)
                    await d_add_files(dThreadMsg, msg_dir[replyTime].files)
                    time.sleep(THROTTLE_TIME_SECONDS)

        print("Migration complete!")
        await ctx.send("[slack2discord] Migration complete!")


if __name__ == "__main__":
    bot = commands.Bot(command_prefix=BOT_PREFIX, intents=discord.Intents.all())
    if TOKEN_VAR not in os.environ:
        print("Please set the token as an environment variable")
        exit(os.EX_CONFIG)

    register_commands()
    bot.run(os.environ.get(TOKEN_VAR))
