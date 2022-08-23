Learnings
- Discord message length cap is 2000 characters. Slack's is 20 times that.
- Empty messages with files are possible.
- Empty messages with files can be the first message in a thread.
- A message can have multiple files.
- A bot response can have multiple human replies.
- Files uploaded can be of 300 MBs, causing server crashes.
- An untitled file is not necessarily a text file, can be an image.
- A message can have multiple formatted links.

Minor learnings
- Discord threads have names.
- The text formatter library you're using can remove important characters without being told to.
- Slack stores which message has a deleted file.
- A field can be only present in a response if the response exists.


Still not handling
- Discord's API has two classes - one for messages, and other that supports markdown-style links.
- 👍 is an emoji, but `:+1:` is a string.
- `:emoji:` is a string, but `<:emoji_name:emoji_id>` is a custom emoji.