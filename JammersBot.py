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
    current_txt_channel = None
    current_url = ""
    position_of_queue = 0
    loop_type = 0

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
                # Option based on loop status
                # If loop_type is 0, then the queue is not looping and will pop the next song
                # else if the loop_type is 1, then the queue is looping
                # else, will just loop the current song
                if(self.loop_type is 0):
                    self.current_url = self.music_queue.pop()
                elif(self.loop_type is 1):
                    self.position_of_queue = (self.position_of_queue + 1) % (len(self.music_queue))
                    self.current_url = self.music_queue[self.position_of_queue]
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    ydl.download([self.current_url])
                await self.play_audio()
            # When the music queue is empty, set the current song to empty
            else:
                self.current_url = ""

    # Given voice_client, play the audio that is currently downloaded
    # under "music.mp3"
    async def play_audio(self):
        #sound = AudioSegment.from_mp3('song.mp3')
        #sound.export('realsong.wav', format = "wav", parameters = ["-vol", "150"])
        audio = FFmpegPCMAudio('song.mp3')
        self.voice_client.play(audio)
        print('Playing song')
        msg = "Now playing: " + await get_youtube_title(self.current_url)
        await self.send_message(msg=msg)
    
    # Sends a message to the currently set text channel
    async def send_message(self, msg):
        await self.current_txt_channel.send("> " + msg)

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
    
    # Shifts through the loop_type
    async def swap_loop_type(self):
        self.loop_type = (self.loop_type + 1) % 3
        c = 0
        while(True):
            if(c is self.position_of_queue):
                break
            self.music_queue.pop()
            c += 1
        self.position_of_queue = 0

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
    vc = ctx.author.voice.channel
    if(vc is None):
        await client.send_message("You must be connected to a voice channel to queue a song")
        return
    await client.join_voice_channel(vc)
    url = await convert_to_yt(url)
    client.current_txt_channel = (ctx.channel)
    await client.send_message('Adding ' + await get_youtube_title(url) + " to the queue")
    client.music_queue.append(url)

# Converts the given string to a youtube url
async def convert_to_yt(str):
    str = re.sub(" ", "+", str)
    html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + str)
    videos = re.findall(r"watch\?v=(\S{11})", html.read().decode())
    str = ("https://youtube.com/watch?v=" + videos[0])
    return str

# Gets the title of the given YouTube url
async def get_youtube_title(url):
    html = urllib.request.urlopen(url=url)
    title_list = re.findall(r"\"title\" content=\"(.*?)\">", html.read().decode())
    return title_list[0]

@client.command()
async def skip(ctx):
    await client.stop_audio()
    await client.send_message('Skipping to the next song')

@client.command()
async def clear(ctx):
    await client.clear_queue()
    await client.send_message('All songs have been removed from the queue')

@client.command()
async def shuffle(ctx):
    await client.shuffle_queue()
    await client.send_message('Shuffling the queue')

@client.command()
async def loop(ctx):
    await client.swap_loop_type()
    if(client.loop_type is 0):
        client.send_message("The queue is no longer on loop")
    elif(client.loop_type is 1):
        await client.send_message("The queue is now on loop")
    else:
        await client.send_message("The current song is now on loop")

@client.command()
async def queue(ctx):
    if(client.current_url is ""):
        ctx.send("Nothing is currently playing")
        return
    url = "Currently playing: " + await get_youtube_title(url=client.current_url) + "\n"
    count = 1
    for song in client.music_queue:
        url += str(count) + ") "
        url += await get_youtube_title(url=song)
        url += "\n"
        count += 1
    await client.send_message(url)

@client.command()
async def remove(ctx, arg):
    try:
        print("HI")
        if(int(arg)-1 < len(client.music_queue)):
            print("HII")
            pos = int(arg) - 1
            await client.send_message("Removed " + get_youtube_title(client.music_queue.pop(pos)))
        else:
            await client.send_message("Not a valid position in the queue")
    except:
        c = 0
        url = ""
        for song in client.music_queue:
            title = await get_youtube_title(song)
            if(str.lower(arg) in str.lower(title)):
                url = song
                break
            elif(c is len(client.music_queue)-1):
                await client.send_message("Song not found in queue")
                return
            c += 1
        client.music_queue.remove(url)

client.run('API TOKEN') #MusicBot
