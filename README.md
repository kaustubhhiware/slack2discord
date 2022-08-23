# slack2discord

Migrate entire slack channels to discord, with thread, pins and file support.

## Table of Contents

1. [Usage](#usage)
2. [Creating a Discord bot](#creating-a-discord-bot)
3. [ToDo](#todo)
4. [Why](#why)
5. [Acknowledgements](#acknowledgements)
6. [License](#license)

## Usage

1. Create a slack export for your workspace. [Slack's official documentation](https://slack.com/help/articles/201658943-Export-your-workspace-data) is simple to follow.
2. Create a Discord bot. Explained [below](#creating-a-discord-bot). You'll get a token here to use later.
3. Copying over users and channel structure.

    a. Make all channels on Discord, as they were on Slack. This is useful for cross-referencing later.

    b. Invite all users from Slack to Discord, maintaining the names.

    c. Add all custom added emojis in Slack to Discord as well. There are tools available to bulk download all emojis in your Slack workspace. Discord allows selecting multiple emojis to upload.

4. Install dependencies.
```
pip3 install -r requirements.txt
```
5. Set the bot token as an environment variable in your terminal. This is read by the script internally.
```
export S2DTOKEN="YOUR-TOKEN-HERE"
```
6. Run the program in the same terminal.
```
python3 migrate.py
```
7. Test the bot is functional. In any channel, type
```
s2d!hi
```

The bot should respond with 
```
Hello there !
```
8. Start the import. In the discord channel you want to import `slack_channel_name`, run this
```
s2d!migrate path/to/extracted/slack/export slack_channel_name
```

Your slack export would look like this.
```
Export
- channel_1
- channel_2
...
- channels.json
- users.json
```
The script uses `channels.json` & `users.json` for cross-reference.

You can import multiple slack channels into one discord channel.
```
s2d!migrate path/to/extracted/slack/export channel1 channel 2
```

The available commands are visible with a help command.
```
s2d!help
```

### Test
**ToDo** You can execute a test run by creating a test channel on discord, and using the `sample` directory as an example.
```
$ git clone https://github.com/kaustubhhiware/slack2discord.git
$ cd slack2discord
// run all steps mentioned above.

// On Discord's #test channel
s2d!migrate path/to/slack2discord/sample general
```

If all looks good, you can run the actual channel-wise migration.


## Creating a Discord bot
Disclaimer: If you've never created a discord bot before, this will test your patience. It involves a lot of back and forth of tweaking something, checking if it works, the bot not working, you questioning your life decisions, you questioning my life decisions, crying, and then trying again. **And that's okay**. It took me 3 hours, but you'll be done in 3 minutes. We'll get through this together.

1. Create a Discord bot on [Discord's Developer Portal](https://discord.com/developers/applications) under the name `slack2discord` (or whatever you prefer).
2. Add an app icon, because this icon would appear when the bot posts all the messages.
3. On the left side panel, let's head to `Bot` section. Hit `Add Bot`.
4. On the Bot page, set an icon and the username again. Turn on the following toggles:

    i. Public bot.

    ii. Presence intent.

    iii. Server members intent.

    iv. Message content intent.

5. Under the `Bot permissions` box, select `Administrators` permission. This will allow us to send messages, create threads, send messages in threads, add emojis, pin messages, etc.
6. Below the username, Click `Reset Token`. Copy this token, you're going to use this later.
7. On the left side panel, Head to `OAuth2 > URL Generator`. Select `bot` scope, and then `Administrators`. Copy the URL generated at the bottom.
8. Head to `OAuth2 > General`. Under `Default Authorization Link`, choose `Custom URL`, and paste the copied URL.
9. Enter the copied URL into a new browser tab, and invite the bot into your Discord server.
10. You should see the bot added on Discord, and we're all done with this step.
11. If the bot doesn't work, go back and check all the things above are as we want. Some of the toggles on 4th step might not be saved. After making all changes, on the `Bot page` hit reset token and retry with the new token.

## ToDo

- [ ] Links
    - Discord doesn't allow hyperlinks in messages, but allows it in embeds [SO answer](https://stackoverflow.com/a/64529788). However, embeds don't have message methods - so need to find a good middle ground.
- [ ] Emojis
    - Discord requires sending the actual emoji, not the text equivalent like `:+1:`. Figure out how to do that.
    - Further, custom emojis require being sent with its id. [FAQ](https://discordpy.readthedocs.io/en/stable/faq.html#how-can-i-add-a-reaction-to-a-message)
- [ ] Test data

## Why

In July 2022, Slack [announced](https://techcrunch.com/2022/07/18/slack-is-increasing-prices-and-changing-the-way-its-free-plan-works/) changes to the free plan. Instead of retaining the last 10,000 messages; it will now retain only the last 3 months of messages.

While the change is okay (even good) for large communities; for people who use it for threads, reminders and the channel structure - for personal use - this was devastating. For me:

1. It would have taken me 5 years to hit the 10,000 messages limit in my personal slack.
2. I enjoy using slack. I understand people use different apps for tracking productivity, but slack has been productive for me - for finances, for learning, for general task tracking.
3. I feel this is a fundamental violation of the contract with Slack. I started using my personal slack in April 2021 with the impression of last 10,000 messages being available (as was the case since 2016, until now). So I'm moving away from Slack out of principle.

I checked a few repositories that handled the migration, but none were to my liking. I spent 4 hours on one repository with 40 stars, and it didn't work. Fine, I'll write the bot myself.

## Acknowledgements

- @rslavin for [rslavin/slack2discord](https://github.com/rslavin/slack2discord), the inspiration for this. It's a great bot, but I insist on maintaining the threads.

## License

The GNU GENERAL PUBLIC LICENSE 2007 - [Kaustubh Hiware](https://github.com/kaustubhhiware). Please have a look at the [LICENSE.md](LICENSE.md) for more details.