#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from plugins.cbb import *
from config import *
from helper_func import encode, get_message_id
import requests
from database.database import *
from io import BytesIO

# Replace this with your actual OMDb API key
OMDB_API_KEY = "601c408a"

@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('batch'))
async def batch(client: Client, message: Message):
    while True:
        try:
            first_message = await client.ask(text = "Forward the First Message from DB Channel (with Quotes)..\n\nor Send the DB Channel Post Link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        f_msg_id = await get_message_id(client, first_message)
        if f_msg_id:
            break
        else:
            await first_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue

    while True:
        try:
            second_message = await client.ask(text = "Forward the Last Message from DB Channel (with Quotes)..\nor Send the DB Channel Post link", chat_id = message.from_user.id, filters=(filters.forwarded | (filters.text & ~filters.forwarded)), timeout=60)
        except:
            return
        s_msg_id = await get_message_id(client, second_message)
        if s_msg_id:
            break
        else:
            await second_message.reply("❌ Error\n\nthis Forwarded Post is not from my DB Channel or this Link is taken from DB Channel", quote = True)
            continue


    string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]])
    await second_message.reply_text(f"<b>Here is your link</b>\n\n{link}", quote=True, reply_markup=reply_markup)


import imdb
import re
import asyncio
from pyrogram import Client, filters

# IMDb Function - Fetches movie details
async def get_movie_details(movie_name):
    ia = imdb.IMDb()
    movies = ia.search_movie(movie_name)

    if not movies:
        return None  

    movie = movies[0]  # Take the first result
    movie_id = movie.movieID
    movie_data = ia.get_movie(movie_id)

    return {
        "title": movie_data.get("title"),
        "year": movie_data.get("year"),
        "poster": movie_data.get("full-size cover url", ""),  # High-resolution poster
        "plot": movie_data.get("plot outline", "No description available."),
        "id": movie_id
    }

# `/genlink` Command - Fetch IMDb details and ask customization questions manually
@Bot.on_message(filters.private & filters.command('genlink'))
async def link_generator(client, message):
    while True:
        try:
            # Ask for movie name
            movie_query = await client.ask(
                text="Send the Movie Name to search IMDb and generate the link.",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=60
            )
        except:
            return

        movie_name = movie_query.text.strip()
        imdb_data = await get_movie_details(movie_name)

        if not imdb_data:
            await movie_query.reply("❌ Movie not found on IMDb. Try again with a different name.", quote=True)
            continue

        movie_title = imdb_data.get("title")
        movie_year = imdb_data.get("year")
        movie_poster = imdb_data.get("poster")  # Automatically fetch IMDb poster
        movie_plot = imdb_data.get("plot", "No description available.")

        # Shorten plot to first sentence
        short_plot = movie_plot.split(". ")[0] + "." if "." in movie_plot else movie_plot

        # **Automatically replace poster with IMDb poster**
        await message.reply_photo(
            photo=movie_poster, 
            caption=f"**{movie_title} ({movie_year})**\n➤ **Details:** {short_plot}",
            quote=True
        )

        # Ask for language
        language_query = await client.ask(
            text="Enter the language (e.g., Hindi, English, Tamil, Telugu):",
            chat_id=message.from_user.id,
            filters=filters.text,
            timeout=60
        )
        movie_language = language_query.text.strip()

        # Ask for quality
        quality_query = await client.ask(
            text="Enter the quality (e.g., HDRip, WEB-DL, 1080p, 720p):",
            chat_id=message.from_user.id,
            filters=filters.text,
            timeout=60
        )
        movie_quality = quality_query.text.strip()

        # Final confirmation
        await message.reply(
            f"🎬 **Movie:** {movie_title} ({movie_year})\n"
            f"📌 **Language:** {movie_language}\n"
            f"📽 **Quality:** {movie_quality}\n\n"
            f"Generating file link... Please wait."
        )

        # Fetch download links from DB
        db_results = await db.get_session(movie_title)
        if not db_results:
            await message.reply("🚫 No download links available in the database.")
            return

        # Generate file links
        caption = f"**{movie_title} ({movie_year})**\n📌 **Language:** {movie_language}\n📽 **Quality:** {movie_quality}\n\n"
        links = {}

        for msg in db_results:
            quality = await check_qualities(msg.text, ["HDRip", "WEB-DL", "1080p", "720p"])
            msg_id = msg.message_id
            encoded = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
            link = f"https://t.me/{BOT_USERNAME}?start={encoded}"

            if quality in links:
                links[quality].append(link)
            else:
                links[quality] = [link]

        for quality, link_list in links.items():
            caption += f"📥 **{quality}**: [Download]({link_list[0]})\n"

        await message.reply(caption, disable_web_page_preview=True)
        break

# Extract quality from caption
async def check_qualities(text, qualities):
    for quality in qualities:
        if quality.lower() in text.lower():
            return quality
    return None