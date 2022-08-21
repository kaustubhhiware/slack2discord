#!/usr/bin/env python3
from concurrent.futures import thread
import json
import os
import time
from datetime import datetime
import discord
from discord.ext import commands
from collections import OrderedDict

THROTTLE_TIME_SECONDS = 1
TOKEN_VAR = "S2DTOKEN"
BOT_PREFIX = "s2d!"

class Message:
    def __init__(self, timestamp, text, user):
        self.timestamp = timestamp
        self.text = text
        self.user = user

    async def print(ctx):
        # format message properly
        # like [Doc](link) shared here 
        # ToDo: emojis
        await ctx.send("")

    async def printInThread(ctx, thread):
        # this is the discord thread that's already created
        # thread = ctx.Guild.get_thread(thread_id)
        await thread.send("")


class Thread:
    def __init__(self, timestamp, text, user, replyTimes):
        self.timestamp = timestamp
        self.message = Message(timestamp, text, user)
        self.replyTimes = replyTimes
        self.replyMessages = list()
        self.isThread = True
        # ToDo: emojis - need to have all slackmojis in discord

    def addReply(self, message):
        self.replyMessages.append(message)

    def markAsReply(self):
        self.isThread = False


def build_msg_dir(fpaths):
    '''
    returned object
    Dict of timestamp to Thread object
    timestamp key
    text
    user
    replies - Message object
    '''
    threads = OrderedDict()


    # add reply timestamps to the threads

    # add replymessages to the thread
    # remove replies as individual threads

    return threads


def get_users(dir):
    userfile = os.path.join(dir, 'users.json')
    if not os.path.exists(userfile):
        return None

    userMap = dict() # map of user id to display name
    try:
        with open(userfile, encoding="utf-8") as f:
            users = json.load(f)
            for user in users:
                username = user['profile']['display_name']
                if not username:
                    username = user['profile']['real_name']
                userMap[user['id']] = username
    except Exception as e:
        return None

    return userMap


def get_channels(dir):
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
            if not os.path.exists(os.path.join(dir, channel)):
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

        channels = get_channels(dir, channelNames)
        if not channels:
            await ctx.send(f"Channels don't seem right. Check channels.json in your directory")
            return

        filepaths = get_filepaths(dir, channelNames)

        # build a list of threads, build later
        msg_dir = build_msg_dir(filepaths)
        # await ctx.send("Import")
        
        # print messages
        # create threads - store ids with timestamp
        # send messages in threads
        # ToDo: pinned messages


if __name__ == "__main__":
    bot = commands.Bot(command_prefix="s2d!", intents=discord.Intents.all())
    if TOKEN_VAR not in os.environ:
        print("Please set the token as an environment variable")
        exit(os.EX_CONFIG)

    register_commands()
    bot.run(os.environ.get('S2DTOKEN'))