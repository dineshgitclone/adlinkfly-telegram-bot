from webserver import keep_alive
from dotenv import load_dotenv
from urllib.parse import quote
import json
import os
import re
import requests
import telebot
from PIL import Image
from io import BytesIO
import pytesseract

# Load environment variables
load_dotenv()

DOMAIN = os.getenv('DOMAIN_NAME')
API_KEY = os.getenv('BOT_TOKEN')
ADLINKFLY_KEY = os.getenv('ADLINKFLY_TOKEN')
START = os.getenv('START')
HELP = os.getenv('HELP')
START_MESSAGE = START.replace("\\n", "\n")
HELP_MESSAGE = HELP.replace("\\n", "\n")

bot = telebot.TeleBot(API_KEY)

# Function for No Ads shortening API call
def shorten_link(link):
    try:
        r = requests.get(f'https://{DOMAIN}/api?api={ADLINKFLY_KEY}&url={link}&type=0')
        if r.status_code == 200:
            response = json.loads(r.text)
            return response['shortenedUrl']
        else:
            print(f'Request failed with status code: {r.status_code}')
            print(f'Response content: {r.text}')
            return None
    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return None

# Function for With Ads shortening API call
def shorten_link_withads(link):
    try:
        r = requests.get(f'https://{DOMAIN}/api?api={ADLINKFLY_KEY}&url={link}')
        if r.status_code == 200:
            response = json.loads(r.text)
            return response['shortenedUrl']
        else:
            print(f'Request failed with status code: {r.status_code}')
            print(f'Response content: {r.text}')
            return None
    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return None

# Function to check if the URL is valid
def is_valid_url(link):
    url_regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE)
    return url_regex.match(link)

# Function to extract URLs from text
def extract_urls(text):
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return urls

# Function to process and shorten multiple links
def process_bulk_links(links, with_ads=False):
    shortened_links = []
    for link in links:
        if is_valid_url(link):
            shortened_link = shorten_link_withads(link) if with_ads else shorten_link(link)
            if shortened_link:
                shortened_links.append(shortened_link)
            else:
                shortened_links.append(f'Failed to shorten: {link}')
        else:
            shortened_links.append(f'Invalid URL: {link}')
    return shortened_links

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        START_MESSAGE,
        parse_mode='Markdown',
        disable_web_page_preview=True)
    bot.send_message(
        message.chat.id,
        "Yay! I'm too excited to see you..!!\nJust send me a link to see the magic..."
    )

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(
        message,
        HELP_MESSAGE,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

@bot.message_handler(commands=['ads'])
def handle_nometa_command(message):
    bot.send_message(
        chat_id=message.chat.id,
        text="Please send the link to shorten without URL metadata!")
    bot.register_next_step_handler(message, handle_bulk_or_text)

def handle_bulk_or_text(message):
    if message.text:
        links = extract_urls(message.text)
        if links:
            bot.send_message(message.chat.id, "Processing links! Please wait...")
            with_ads = True  # Set to False if you want no-ads shortening
            shortened_links = process_bulk_links(links, with_ads)
            response_message = "\n".join(shortened_links)
            bot.reply_to(message, response_message, parse_mode='Markdown', disable_web_page_preview=True)
        else:
            bot.send_message(message.chat.id, "No valid URLs found in the message.")
    else:
        bot.send_message(message.chat.id, "Please send a valid message containing links.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    links = extract_urls(message.text)
    if links:
        bot.send_message(message.chat.id, "Processing links! Please wait...")
        shortened_links = process_bulk_links(links)
        response_message = "\n".join(shortened_links)
        bot.reply_to(message, response_message, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "No valid URLs found in the message.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    image = Image.open(BytesIO(downloaded_file))
    text = pytesseract.image_to_string(image)
    links = extract_urls(text)
    if links:
        bot.send_message(message.chat.id, "Processing links from image! Please wait...")
        shortened_links = process_bulk_links(links)
        response_message = "\n".join(shortened_links)
        bot.reply_to(message, response_message, parse_mode='Markdown', disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "No valid URLs found in the image.")

keep_alive()
bot.polling()
