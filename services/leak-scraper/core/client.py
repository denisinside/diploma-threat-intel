"""
Telethon client initialization and authentication.
"""
import asyncio
import warnings
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SessionPasswordNeededError
from telethon.tl.types import PeerChannel, Channel, Chat
from loguru import logger

warnings.filterwarnings("ignore", message="Using async sessions support is an experimental feature")


async def create_client(
    api_id: int, api_hash: str, session_name: str, session_path: str = ""
) -> TelegramClient:
    """Create and connect Telegram client. Use session_path for Docker volume persistence."""
    name = str(Path(session_path) / session_name) if session_path else session_name
    client = TelegramClient(name, api_id, api_hash)
    await client.connect()
    return client


async def ensure_authorized(client: TelegramClient) -> bool:
    """Ensure client is authorized. Returns True if authorized."""
    if await client.is_user_authorized():
        logger.info("Telegram client already authorized")
        return True

    logger.info("Telegram client not authorized. Use QR or phone auth.")
    # QR code auth
    try:
        qr_login = await client.qr_login()
        logger.info("Scan QR code with Telegram app: Settings > Devices > Link Desktop Device")
        import qrcode
        from io import StringIO
        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(qr_login.url)
        qr.make()
        f = StringIO()
        qr.print_ascii(out=f)
        f.seek(0)
        print(f.read())

        await qr_login.wait()
        logger.info("QR login successful")
        return True
    except SessionPasswordNeededError:
        password = input("2FA password: ")
        await client.sign_in(password=password)
        logger.info("2FA login successful")
        return True
    except Exception as e:
        logger.error(f"QR auth failed: {e}. Try phone auth.")
        phone = input("Phone number: ")
        await client.send_code_request(phone)
        code = input("Code: ")
        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("2FA password: ")
            await client.sign_in(password=password)
        return True


async def get_entity(client: TelegramClient, channel_id: str):
    """Resolve channel/chat entity by ID or username. Handles FloodWaitError."""
    for attempt in range(5):
        try:
            if channel_id.lstrip("-").isdigit():
                return await client.get_entity(PeerChannel(int(channel_id)))
            return await client.get_entity(channel_id)
        except FloodWaitError as e:
            logger.warning(f"FloodWait on get_entity: waiting {e.seconds}s")
            await asyncio.sleep(e.seconds)
    raise RuntimeError("get_entity failed after FloodWait retries")
