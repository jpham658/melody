from dotenv import load_dotenv
from discord.ext import commands
from discord.ext.commands import errors
import wavelink
import discord
import os
load_dotenv()

# Music cog
class MusicCog(commands.Cog):
    EMBED_COLOUR: discord.Colour = 0xE5BED0

    def __init__(self, bot: commands.Bot) -> None:
        """Constructor for the MusicCog."""
        commands.Cog.__init__(self)
        self.__bot: commands.Bot = bot
        self.__player: wavelink.Player = None
        self.bot.loop.create_task(self.node_connect())

    @property 
    def bot(self) -> commands.Bot:
        return self.__bot
    
    @property
    def player(self) -> wavelink.Player:
        return self.__player
    
    @player.setter 
    def player(self, value: wavelink.Player) -> None:
        self.__player = value

    # Song manipulation commands

    @commands.command(name="play")
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack | wavelink.YouTubePlaylist = None) -> discord.Message:
        """
        Plays the track or playlist the user has given.

        :param search: The YouTube track or playlist to be played. 
        :return: A Message object describing if the player is playing anything.
        """
        if not search:
            raise NoneSearchError
        if not ctx.voice_client and not ctx.author.voice:
            raise NoneVoiceChannelError

        vc: discord.VoiceChannel = ctx.voice_client if ctx.voice_client else ctx.author.voice.channel

        if not self.player or not self.player.is_connected():
            await self.__player_connect(vc)
        player: wavelink.Player = self.player

        if player.is_paused():
            raise PlayerPausedError
        
        if isinstance(search, wavelink.YouTubeTrack):
            embed: discord.Embed = self.__create_songs_embed(search)

            if player.queue.is_empty and not player.is_playing():
                await player.play(search)
                return await ctx.send(content="Currently playing:", embed=embed)
            else:
                await player.queue.put_wait(search)
                return await ctx.send(content="Queued:", embed=embed)
        else:
            embed: discord.Embed = self.__create_songs_embed(search)
            await player.queue.put_wait(search)
            
            if not player.queue.is_empty and not player.is_playing():
                track: wavelink.YouTubeTrack = await player.queue.get_wait()
                await player.play(track)
                return await ctx.send(
                    content="Currently playing playlist:", embed=embed
                )
            else:
                return await ctx.send(content="Queued:", embed=embed)
    
    @play.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, NoneSearchError):
            await ctx.send("Please enter a song to play.")
        elif isinstance(err, NoneVoiceChannelError):
            await ctx.send("Please enter a voice channel first!")
        elif isinstance(err, PlayerPausedError):
            await ctx.send("The player is paused! Use `!resume` to play new songs.")
        else:
            await ctx.send("There was a problem with your command. Try again!")

    @commands.command(name="pause")
    async def pause(self, ctx: commands.Context) -> discord.Message:
        """
        Pause the current track playing.

        :return: A Message object describing if the player has paused.
        """
        if not ctx.voice_client and not ctx.author.voice:
            raise NoneVoiceChannelError

        vc: discord.VoiceChannel = ctx.voice_client if ctx.voice_client else ctx.author.voice.channel
       
        if not self.player or not self.player.is_connected():
            self.__player_connect(vc)

        player: wavelink.Player = self.player

        if not player.current:
            raise NothingPlayingError
        elif player.is_paused():
            raise PlayerPausedError

        await player.pause()
        return await ctx.send(
            f"Paused {self.player.current.title} by {self.player.current.author}"
        )
    
    @pause.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, NoneVoiceChannelError):
            await ctx.send("Please enter a voice channel first!")
        elif isinstance(err, NothingPlayingError):
            await ctx.send("You aren't playing anything!")
        elif isinstance(err, PlayerPausedError):
            await ctx.send("Player is already paused.")
        else:
            await ctx.send("There was a problem with your command. Try again!")

    @commands.command(name="resume")
    async def resume(self, ctx: commands.Context) -> discord.Message:
        """
        Resume playing a track that was paused.

        :return: A Message object describing if the player resumed playing.
        """
        if not ctx.voice_client and not ctx.author.voice:
            raise NoneVoiceChannelError

        vc: discord.VoiceChannel = ctx.voice_client if ctx.voice_client else ctx.author.voice.channel

        if not self.player or not self.player.is_connected():
            self.__player_connect(vc)
        player: wavelink.Player = self.player

        if not player.current:
            raise NothingPlayingError
        elif not player.is_paused():
            raise PlayerPlayingError

        await player.resume()
        return await ctx.send(
            f"Resumed playing {self.player.current.title} by {self.player.current.author}"
        )
    
    @resume.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, NoneVoiceChannelError):
            await ctx.send("Please enter a voice channel first!")
        elif isinstance(err, NothingPlayingError):
            await ctx.send("You aren't playing anything!")
        elif isinstance(err, PlayerPlayingError):
            await ctx.send("You're already playing something!")
        else:
            await ctx.send("There was a problem with your command. Try again!")
    
    @commands.command(name="skip")
    async def skip(self, ctx: commands.Context) -> discord.Message:
        """
        Skip the song currently playing.

        :return: A Message object describing if the current song has been skipped.
        """
        player: wavelink.Player = self.player

        if not player or not player.is_connected():
            raise PlayerNotConnectedError
        if player.queue.is_empty and not player.current:
            raise EmptyPlayerQueueError

        await player.stop()
        return await ctx.send("Skipped song!")
    
    @skip.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, PlayerNotConnectedError):
            await ctx.send("Player isn't connected. Join a VC and try again!")
        elif isinstance(err, EmptyPlayerQueueError):
            await ctx.send("Queue is empty; nothing to skip here!")
        else:
            await ctx.send("There was a problem with your command. Try again!")
    
    # Information commands

    @commands.command(name="song")
    async def song(self, ctx: commands.Context) -> discord.Message:
        player: wavelink.Player = self.player

        if not player or not player.is_connected():
            raise PlayerNotConnectedError
        
        if not player.current:
            raise NothingPlayingError

        embed: discord.Embed = self.__create_songs_embed(self.player.current)
        return await ctx.send(content="Currently playing:", embed=embed)
    
    @song.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, PlayerNotConnectedError):
            await ctx.send("Player isn't connected. Join a VC and try again!")
        elif isinstance(err, NothingPlayingError):
            await ctx.send("Nothing is playing currently.")
        else:
            await ctx.send("There was a problem with your command. Try again!")

    @commands.command(name="queue")
    async def queue(self, ctx: commands.Context) -> discord.Message:
        """
        View the player's queue.

        :return: A Message object describing the queue's current state.
        """
        player: wavelink.Player = self.player

        if not player or not player.is_connected():
            raise PlayerNotConnectedError

        if player.queue.is_empty:
            raise EmptyPlayerQueueError
        
        embed: discord.Embed = self.__create_queue_embed(self.player.queue)
        return await ctx.send(content="Queue:", embed=embed)
    
    @queue.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, PlayerNotConnectedError):
            await ctx.send("Player isn't connected. Join a VC and try again!")
        elif isinstance(err, EmptyPlayerQueueError):
            await ctx.send("Queue is empty!")
        else:
            await ctx.send("There was a problem with your command. Try again!")

    # Queue manipulation commands

    @commands.command(name="remove")
    async def remove(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack | wavelink.YouTubePlaylist = None) -> discord.Message:
        if not search:
            raise NoneSearchError
        
        player: wavelink.Player = self.player

        if not player or not player.is_connected():
            raise PlayerNotConnectedError
        
        if not player.queue or player.queue.is_empty:
            raise EmptyPlayerQueueError
        
        if not search in player.queue:
            raise NotInQueueError
        
        index: int = player.queue.find_position(search)
        del player.queue[index]
        await ctx.send(f"Successfully removed '{search.title} by {search.author}' from queue.")
    
    @remove.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, NoneSearchError):
            await ctx.send("Please enter a song to play.")
        elif isinstance(err, PlayerNotConnectedError):
            await ctx.send("Player isn't connected. Join a VC and try again!")
        elif isinstance(err, EmptyPlayerQueueError):
            await ctx.send("Queue is empty, could not remove the track!")
        elif isinstance(err, NotInQueueError):
            await ctx.send("This track is not in the queue.")
        else:
            await ctx.send("There was a problem with your command. Try again!")

    @commands.command(name="shuffle")
    async def shuffle(self, ctx: commands.Context) -> discord.Message:
        """
        Shuffle the player's queue.

        :return: A Message object describing if the queue has been shuffled.
        """
        player: wavelink.Player = self.player

        if not player or not player.is_connected():
            raise PlayerNotConnectedError

        if not player.queue or player.queue.is_empty:
            raise EmptyPlayerQueueError

        player.queue.shuffle()
        await ctx.send("Shuffled the queue!")
        embed: discord.Embed = self.__create_queue_embed(self.player.queue)
        return await ctx.send(content="Queue:", embed=embed)
    
    @shuffle.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, PlayerNotConnectedError):
            await ctx.send("Player isn't connected. Join a VC and try again!")
        elif isinstance(err, EmptyPlayerQueueError):
            await ctx.send("Queue is empty!")
        else:
            await ctx.send("There was a problem with your command. Try again!")
    
    @commands.command(name="clear")
    async def clear(self, ctx: commands.Context) -> discord.Message:
        player: wavelink.Player = self.player

        if not player or not player.is_connected():
            raise PlayerNotConnectedError

        if player.queue.is_empty:
            raise EmptyPlayerQueueError

        player.queue.reset()
        return await ctx.send("Queue is now empty.")
    
    @clear.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, PlayerNotConnectedError):
            await ctx.send("Player isn't connected. Join a VC and try again!")
        elif isinstance(err, EmptyPlayerQueueError):
            await ctx.send("Queue is empty!")
        else:
            await ctx.send("There was a problem with your command. Try again!")
    
    # Player manipulation commands

    @commands.command(name="volume")
    async def volume(self, ctx: commands.Context, volume: int) -> discord.Message:
        if volume < 0 or volume > 150:
            raise OutOfBoundsError
        
        if not self.player or not self.player.is_connected():
            raise PlayerNotConnectedError
        
        await self.player.set_volume(volume)
        return await ctx.send(f"Successfully set player volume to {volume}!")
    
    @volume.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, PlayerNotConnectedError):
            await ctx.send("Player isn't connected. Join a VC and try again!")
        elif isinstance(err, OutOfBoundsError):
            await ctx.send("Please enter a volume between 0-150 (inclusive).")
        else:
            await ctx.send("There was a problem with your command. Try again!")

    @commands.command(name="disconnect")
    async def disconnect(self, ctx: commands.Context) -> discord.Message:
        """
        The bot will leave the voice channel if connected and
        stop playing music.

        :return: A Message object describing if the player has disconnected from VC.
        """
        if not self.player or not self.player.is_connected():
            raise PlayerNotConnectedError

        await ctx.voice_client.disconnect()
        return await ctx.send("Successfully disconnected from VC.")

    @disconnect.error
    async def on_command_error(self, ctx: commands.Context, err: errors.CommandError) -> None:
        if isinstance(err, PlayerNotConnectedError):
            await ctx.send("I'm not connected to VC.")
        else:
            await ctx.send("There was a problem with your command. Try again!")

    # Listeners

    @commands.Cog.listener()
    async def on_ready(self):
        print("MusicCog is ready.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.errors.CommandError):
        if isinstance(error, commands.errors.CommandNotFound):
            await ctx.send("This command is not supported. Use `!help` to see what commands are supported.")
        elif isinstance(error, commands.errors.CommandInvokeError):
            print("invoke error")
    @commands.Cog.listener()
    async def on_disconnect(self):
        if self.player and self.player.is_connected():
            await self.player.disconnect()
            print("Player disconnected.")
        else:
            print("Player could not be disconnected.")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node) -> None:
        print(f"Node {node.id} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackEventPayload):
        print(f"Player has started playing a track.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        print(f"Player has finished playing a track.\n")
        if not self.player.queue.is_empty:
            next_track: wavelink.YouTubeTrack = await self.player.queue.get_wait()
            await self.player.play(next_track)
        else:
            print("Queue is empty.")

    @commands.Cog.listener()
    async def on_wavelink_websocket_closed(
        self, payload: wavelink.WebsocketClosedPayload
    ):
        print(f"Websocket has closed successfully.")

    async def node_connect(self):
        """Connect node to the Lavalink server."""
        await self.bot.wait_until_ready()
        NODE_HOST = os.getenv("NODE_HOST")
        NODE_PASSWORD = os.getenv("NODE_PASSWORD")
        node: wavelink.Node = wavelink.Node(
            uri=NODE_HOST, password=NODE_PASSWORD, use_http=True
        )
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    async def __player_connect(self, vc: discord.VoiceChannel) -> None:
        """
        Creates and connects player to a voice channel.
        
        :param vc: The voice channel we will connect to.
        """
        player: wavelink.Player = await vc.connect(
                timeout=90, reconnect=False, cls=wavelink.Player
            )
        print("connected player")
        self.player = player
        print("set player")

    def __create_queue_embed(self, queue: wavelink.Queue) -> discord.Embed:
        queue_list: str = ""
        for track in queue:
            queue_list += f"- {track.title} by {track.author}\n"

        embed: discord.Embed = discord.Embed(
            colour=self.EMBED_COLOUR,
            title="Queue:",
            description=queue_list
        )
        return embed
    
    def __create_songs_embed(
        self, search: wavelink.YouTubeTrack | wavelink.YouTubePlaylist
    ) -> discord.Embed:
        if isinstance(search, wavelink.YouTubeTrack):
            embed: discord.Embed = discord.Embed(
                colour=self.EMBED_COLOUR,
                title=f"{search.title} by {search.author}",
                description=f"{search.title}",
                url=search.uri,
            )
            return embed
        else:
            tracklist: str = "".join(
                f"{search.tracks.index(song)}. {song.title} by {song.author}\n"
                for song in search.tracks
            )
            embed: discord.Embed = discord.Embed(
                colour=self.EMBED_COLOUR,
                title=f"{search.name}",
                description=f"{tracklist}",
            )
            return embed
        
# Exception classes
class NoneSearchError(errors.CommandError):
    pass

class NoneVoiceChannelError(errors.CommandError):
    pass

class PlayerPausedError(errors.CommandError):
    pass

class NothingPlayingError(errors.CommandError):
    pass

class PlayerPlayingError(errors.CommandError):
    pass

class PlayerNotConnectedError(errors.CommandError):
    pass

class EmptyPlayerQueueError(errors.CommandError):
    pass

class OutOfBoundsError(errors.CommandError):
    pass

class NotInQueueError(errors.CommandError):
    pass

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicCog(bot))