import os
import logging
import json
import asyncio
from openai import OpenAI
import nats
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils import executor

# Load API Keys
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NATS_SERVER = os.getenv("NATS_SERVER", "nats://nats:4222")

# Initialize bot & logging
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)



# NATS Client
nc = None

async def connect_nats():
    """Connect to NATS server."""
    global nc
    nc = await nats.connect(NATS_SERVER)
    logging.info("✅ Connected to NATS!")

    # Subscribe to refund response messages
    await nc.subscribe("refund_responses", cb=handle_nats_response)

async def handle_nats_response(msg):
    """Handles refund decisions from NATS."""
    try:
        data = json.loads(msg.data.decode())
        chat_id = data["chat_id"]
        decision = data["decision"]

        response_text = {
            "approved": "✅ Your refund has been **APPROVED**!",
            "manual_review": "🟡 Your request is under **manual review**.",
            "denied": "❌ Your refund request has been **DENIED**."
        }

        # Send response to Telegram user
        await bot.send_message(chat_id, response_text.get(decision, "Error processing request."))

    except Exception as e:
        logging.error(f"NATS Response Error: {e}")

def extract_refund_details(user_message):
    """Uses OpenAI to extract Order ID, Refund Reason, and Amount."""
    prompt = f"""
    Extract refund details from this message:
    "{user_message}"
    
    Output JSON format:
    {{
      "order_id": "<order_id>",
      "reason": "<refund_reason>",
      "amount": <refund_amount>
    }}
    If amount is not mentioned, use 0.
    """

    try:
        print("user_message:", user_message)
        print("prompt:", prompt)

        # OpenAI Setup (Synchronous)
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert at extracting refund details."},
                {"role": "user", "content": prompt}
            ],
            # response_format={"type": "json"}  # Ensure structured JSON output
        )

        print("response:", response)
        refund_data = response.choices[0].message.content
        return json.loads(refund_data)

    except Exception as e:
        logging.error(f"OpenAI Parsing Error: {e}")
        return None

@dp.message_handler(commands=["start"])
async def start(message: Message):
    logging.info("start...")
    await message.reply("🤖 Hello! Send your **refund request** (e.g., 'I want a refund for order 12345 due to damage').")

@dp.message_handler()
async def process_refund(message: Message):
    """Sends refund request to NATS & waits for async response."""
    try:
        logging.info("process_refund")
        refund_details = extract_refund_details(message.text)

        print(refund_details)
        if not refund_details or "order_id" not in refund_details:
            await message.reply("❌ Could not understand your request. Please provide an Order ID & reason.")
            return

        # Prepare NATS message
        request_data = {
            "chat_id": message.chat.id,  # Store Telegram chat ID for response
            "user_id": message.from_user.id,
            "order_id": refund_details["order_id"],
            "reason": refund_details["reason"],
            "amount": refund_details.get("amount", 0)  # Default to 0 if missing
        }
        print(request_data)
        # Publish to NATS
        await nc.publish("refund_requests", json.dumps(request_data).encode())

        await message.reply("⏳ Your refund request is being processed...")

    except Exception as e:
        logging.error(f"Error: {e}")
        await message.reply("⚠ Something went wrong. Try again later.")

async def on_startup(dp):
    """Runs on startup to connect to NATS before polling."""
    await connect_nats()
    logging.info("✅ NATS Connected. Telegram Bot is starting...")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
