#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot import Bot
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



@Bot.on_message(filters.private & filters.user(ADMINS) & filters.command('genlink'))
async def link_generator(client: Client, message: Message):
    while True:
        try:
            # Ask for the movie name
            movie_query = await client.ask(
                text="Send the Movie Name to search IMDb and generate the link.",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=60
            )
        except:
            return
        
        movie_name = movie_query.text.strip()
        imdb_data = await get_movie_details(movie_name)  # Fetch movie details from IMDb
        
        if not imdb_data:
            await movie_query.reply("❌ Movie not found on IMDb. Try again with a different name.", quote=True)
            continue

        movie_title = imdb_data.get("title")
        movie_year = imdb_data.get("year")
        movie_poster = imdb_data.get("poster")
        imdb_id = imdb_data.get("id")
        movie_plot = imdb_data.get("plot", "No description available.")  # Get short plot summary
        
        # Search for the movie in the DB Channel
        db_results = await db.get_session(movie_title)  # Fetch messages with matching movie name
        
        if not db_results:
            await movie_query.reply("❌ No matching files found in the DB Channel.", quote=True)
            continue
        
        # Generate links for each available quality
        links = {}
        for msg in db_results:
            quality = extract_quality(msg.text)  # Extract quality info from the message
            msg_id = msg.message_id
            encoded = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
            link = f"https://t.me/{client.username}?start={encoded}"
            
            if quality in links:
                links[quality].append(link)
            else:
                links[quality] = [link]

        # Prepare caption with the requested format
        caption = f"{movie_title} ({movie_year})\n\n"
        caption += f"➤ <blockquote>{movie_plot}</blockquote>\n\n"

        for quality, link_list in links.items():
            if len(link_list) > 1:
                batch_link = await generate_batch_link(link_list)
                caption += f"📥 {quality}: [Batch Download]({batch_link})\n"
            else:
                caption += f"📥 {quality}: [Download]({link_list[0]})\n"

        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link_list[0]}')]])

        await message.reply_photo(photo=movie_poster, caption=caption, reply_markup=reply_markup, quote=True)
        break



import imdb

async def get_movie_details(movie_name):
    ia = imdb.IMDb()  # Initialize IMDb API
    movies = ia.search_movie(movie_name)  # Search for the movie
    
    if not movies:
        return None  # No results found

    movie = movies[0]  # Take the first result
    movie_id = movie.movieID
    movie_data = ia.get_movie(movie_id)  # Fetch full movie details
    
    return {
        "title": movie_data.get("title"),
        "year": movie_data.get("year"),
        "poster": movie_data.get("cover url", ""),  # Movie poster URL
        "plot": movie_data.get("plot outline", "No description available."),
        "id": movie_id
    }