# Melody Discord Music Bot

Melody is a feature-rich Discord music bot that allows you to play music in your Discord server using the [nextcord](https://github.com/nextcord/nextcord) library and [WaveLink](https://github.com/PythonistaGuild/Wavelink) to interface with a local Lavalink server.

## Features

- High-quality music streaming from YouTube
- Playback controls such as play, pause, skip, etc.
- Queue management with the ability to add and shuffle tracks
- Music search with flexible query options
- Rich music-related commands
- And more!

## Dependencies

To run the Melody bot, you need the following dependencies:

- [Python 3.8+](https://www.python.org/downloads/)
- [discord.py](https://github.com/Rapptz/discord.py)
- [WaveLink](https://github.com/PythonistaGuild/Wavelink)
- [Lavalink Server](https://github.com/lavalink-devs/Lavalink)
- You will also need to get a Discord token by registering the bot on the [Discord developer portal](https://discord.com/developers/applications)

## Commands

Here are the available commands for Melody:

- `!play <song>`: Plays the specified song or adds it to the queue if music is already playing.
- `!pause`: Pauses the current playback.
- `!resume`: Resumes playback if paused.
- `!skip`: Skips the current song and proceeds to the next one in the queue.
- `!shuffle`: Shuffles the songs in the queue.
- `!disconnect`: Disconnects the player from the voice channel.
- `!clear`: Clears the player's queue.
- `!queue`: Displays the current music queue.
- **To be implemented**
- `!remove <index>`: Removes the song at the specified index from the queue.
- `!volume <level>`: Adjusts the playback volume to the specified level.

