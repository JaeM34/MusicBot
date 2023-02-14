import yt_dlp
import discord
from discord.ext import commands
import os
from pydub import AudioSegment
from os import path
from discord import FFmpegPCMAudio
import random
from discord.ext import tasks
import urllib.request
import re

class JammersBot(commands.Bot):

    # Variables
    music_queue = []
    voice_client = None
    current_url = ""

    # Options for the YouTube overlords
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'continue': True,
        'outtmpl': 'song.mp3',
        'extractaudio': 'mp3'
    }
    
    # Chewsday Innit?
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        self.audio_queue.start()

    # a looping task that checks every x seconds
    # whether or not the music bot is playing a song
    # if there is a YouTube url in the music queue and the
    # bot is not playing, pop the url then play the audio
    @tasks.loop(seconds=2)
    async def audio_queue(self):
        # Whenever client is in a voice channel and is playing, queue should be checked
        if(self.voice_client is not None and not self.voice_client.is_playing()):
            # When the music queue is not empty, pop the next song and play the audio
            if(len(self.music_queue) is not 0):
                try:
                    os.remove(os.path.join(os.getcwd(), "song.mp3"))
                except:
                    pass
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    self.current_url = self.music_queue.pop()
                    ydl.download([self.current_url])
                await self.play_audio()
            # When the music queue is empty, set the current song to empty
            else:
                self.current_url = ""

    # Given voice_client, play the audio that is currently downloaded
    # under "music.mp3"
    async def play_audio(self):
        sound = AudioSegment.from_mp3('song.mp3')
        sound.export('realsong.wav', format = "wav", parameters = ["-vol", "150"])
        audio = FFmpegPCMAudio('realsong.wav')
        self.voice_client.play(audio)

    # Used to stop the current track
    async def stop_audio(self):
        self.voice_client.stop()
        self.current_url = ""

    # Clears the queue
    async def clear_queue(self):
        self.music_queue.clear()

    # Shuffles the queue
    async def shuffle_queue(self):
        random.shuffle(self.music_queue)

    # Joins a channel and sets voice_client to connected voice
    async def join_voice_channel(self, channel):
        try:
            self.voice_client = await channel.connect()
        except:
            pass


intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

client = JammersBot(command_prefix = "!", intents = intents)


# Define the !play command
# !play (url)
# When given a url, add the url to the queue

@client.command()
async def play(ctx, *, url):
    url = convert_to_yt(url)
    await ctx.send('Queueing ' + url)
    channel = ctx.author.voice.channel
    await client.join_voice_channel(channel)
    client.music_queue.append(url)

# Converts the given string to a youtube url
def convert_to_yt(str):
    str = re.sub(" ", "+", str)
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + str)
    videos = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    str = ("https://youtube.com/watch?v=" + videos[0])
    return str

# Gets the title of the given YouTube url
def get_youtube_title(url):
    html = urllib.request.urlopen(url=url)
    title_list = re.findall(r"\"title\" content=\"(.*?)\">", html.read().decode())
    return title_list[0]

@client.command()
async def skip(ctx):
    await client.stop_audio()
    await ctx.send('Stopping audio')

@client.command()
async def clear(ctx):
    await client.clear_queue()
    await ctx.send('Cleared queue')

@client.command()
async def shuffle(ctx):
    await client.shuffle_queue()
    await ctx.send('Shuffled queue')

@client.command()
async def queue(ctx):
    if(client.current_url is ""):
        ctx.send("Nothing is currently playing")
        return
    url = "Now playing: " + get_youtube_title(url=client.current_url) + "\n"
    count = 1
    for song in client.music_queue:
        url += str(count) + ") "
        url += get_youtube_title(url=song)
        url += "\n"
        count += 1
    await ctx.send(url)

@client.command()
async def remove(ctx, arg):
    pos = int(arg)
    if(type(pos) is int):
        client.music_queue.remove(pos-1)

client.run("API TOKEN HERE")
