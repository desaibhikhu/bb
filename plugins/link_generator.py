#(©)Codexbotz

from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from bot import Bot
from pyrogram.enums import ParseMode
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


#import imdb
import asyncio
import requests
#from io import BytesIO
#from PIL import Image
from pyrogram import Client, filters
from pyrogram.enums import ParseMode

# Function to upscale image
async def upscale_image(image_url):
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))

        # Resize image using PIL (LANCZOS for best quality)
        width, height = image.size
        image = image.resize((width * 2, height * 2), Image.LANCZOS)

        # Save upscaled image to memory
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="JPEG", quality=95)
        img_byte_arr.seek(0)

        return img_byte_arr
    except Exception as e:
        print(f"Error upscaling image: {e}")
        return None

# IMDb Function - Fetches multiple posters
async def get_movie_details(movie_name):
    ia = imdb.IMDb()
    movies = ia.search_movie(movie_name)

    if not movies:
        return None

    movie = movies[0]  # Take the first result
    movie_id = movie.movieID
    movie_data = ia.get_movie(movie_id)

    # Fetch all poster URLs
    poster_urls = []
    if 'full-size cover url' in movie_data.keys():
        poster_urls.append(movie_data['full-size cover url'])

    if 'cover url' in movie_data.keys():
        poster_urls.append(movie_data['cover url'])

    # Remove duplicates
    poster_urls = list(set(poster_urls))

    return {
        "title": movie_data.get("title"),
        "year": movie_data.get("year"),
        "posters": poster_urls,
        "plot": movie_data.get("plot outline", "No description available."),
        "id": movie_id
    }

# `/genlink` Command - Fetch IMDb details and generate links
@Client.on_message(filters.private & filters.command('genlink'))
async def link_generator(client, message):
    while True:
        try:
            # Step 1: Ask for movie name
            movie_query = await client.ask(
                text="🎬 Send the Movie Name to fetch IMDb details and generate a link.",
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

        # Extract IMDb details
        movie_title = imdb_data.get("title")
        movie_year = imdb_data.get("year")
        imdb_posters = imdb_data.get("posters", [])
        movie_plot = imdb_data.get("plot", "No description available.")
        short_plot = movie_plot.split(". ")[0] + "." if "." in movie_plot else movie_plot

        if not imdb_posters:
            await message.reply("⚠️ No poster found for this movie.")
            return

        # Send first upscaled poster immediately
        movie_poster_url = imdb_posters[0]
        upscaled_poster = await upscale_image(movie_poster_url) or movie_poster_url

        await message.reply_photo(
            photo=upscaled_poster,
            caption=(
                f"🎬 {movie_title} ({movie_year})\n"
                f"📝 {short_plot}"
            ),
            quote=True
        )

        # Step 2: Ask for Language
        try:
            language_msg = await client.ask(
                text="🌐 Select a Language\nType one of the following: `Hindi`, `English`, `Tamil`, `Telugu`",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=60
            )
        except:
            return

        language = language_msg.text.strip().capitalize()
        if language not in ["Hindi", "English", "Tamil", "Telugu"]:
            await message.reply("❌ Invalid language. Using default: `English`.")
            language = "English"

        # Step 3: Ask for Quality
        try:
            quality_msg = await client.ask(
                text="🎥 Select Quality\nType one of: `HDRip`, `WEB-DL`, `1080p`, `720p`",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=60
            )
        except:
            return

        quality = quality_msg.text.strip()
        if quality not in ["HDRip", "WEB-DL", "1080p", "720p"]:
            await message.reply("❌ Invalid quality. Using default: `720p`.")
            quality = "720p"

        # Step 4: Ask if user wants to add a file
        try:
            add_file_msg = await client.ask(
                text="📂 Do you want to upload a file? (Type `yes` or `no`)",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=60
            )
        except:
            return

        if add_file_msg.text.lower() == "no":
            await message.reply("✅ Link generation completed without file upload.")
            return

        # Step 5: Ask if it's a single or batch file
        try:
            file_type_msg = await client.ask(
                text="📁 Is this a `Single` file or `Batch` upload?\n\nType `single` or `batch`.",
                chat_id=message.from_user.id,
                filters=filters.text,
                timeout=60
            )
        except:
            return

        file_type = file_type_msg.text.lower()
        if file_type not in ["single", "batch"]:
            await message.reply("❌ Invalid choice. Assuming `Single` file.")
            file_type = "single"

        if file_type == "single":
            # Single file logic (Using `genlink`)
            try:
                channel_message = await client.ask(
                    text="📤 Forward the Message from the DB Channel or Send the DB Channel Post link.",
                    chat_id=message.from_user.id,
                    filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                    timeout=60
                )
            except:
                return

            msg_id = await get_message_id(client, channel_message)
            if not msg_id:
                await channel_message.reply("❌ Error: Not from the DB Channel.", quote=True)
                return

            base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
            link = f"https://t.me/{client.username}?start={base64_string}"

        else:
            # Batch file logic (Using `batch`)
            try:
                first_message = await client.ask(
                    text="📤 Forward the First Message from the DB Channel or Send the DB Channel Post Link.",
                    chat_id=message.from_user.id,
                    filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                    timeout=60
                )
                f_msg_id = await get_message_id(client, first_message)
                if not f_msg_id:
                    await first_message.reply("❌ Error: Not from the DB Channel.", quote=True)
                    return

                second_message = await client.ask(
                    text="📤 Forward the Last Message from the DB Channel or Send the DB Channel Post Link.",
                    chat_id=message.from_user.id,
                    filters=(filters.forwarded | (filters.text & ~filters.forwarded)),
                    timeout=60
                )
                s_msg_id = await get_message_id(client, second_message)
                if not s_msg_id:
                    await second_message.reply("❌ Error: Not from the DB Channel.", quote=True)
                    return

                string = f"get-{f_msg_id * abs(client.db_channel.id)}-{s_msg_id * abs(client.db_channel.id)}"
                base64_string = await encode(string)
                link = f"https://t.me/{client.username}?start={base64_string}"

            except Exception as e:
                await message.reply(f"⚠️ An error occurred: {e}")
                return

        # Step 7: Generate final caption
        caption = (
            f"🎬 {movie_title} ({movie_year})\n\n"
            f"📝 Plot : {short_plot}\n\n"
            f"🌐 Language: `{language}`\n"
            f"🎥 Quality: `{quality}`\n\n"
            f"📥 {'Click Here' if file_type == 'batch' else 'Download Link'}:\n"
            f"🔗 [Download Here]({link})\n"
        )

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔁 Share URL", url=f'https://telegram.me/share/url?url={link}')]
        ])

        # Step 8: Send final poster with caption
        await message.reply_photo(
            photo=upscaled_poster,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        break