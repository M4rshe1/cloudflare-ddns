import os
import requests
import asyncio
import aiocron
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

API_TOKEN = os.getenv("CF_API_TOKEN")
ZONE_ID = os.getenv("CF_ZONE_ID")
DNS_NAME = os.getenv("CF_DNS_NAME")
IP_PROVIDER = os.getenv("IP_PROVIDER", "ipify")
CRON_SCHEDULE = os.getenv("CRON_SCHEDULE", "*/5 * * * *")
PROXY = os.getenv("PROXY", "false").lower() == "true"

TTL_ENV = os.getenv("TTL", "3600").lower()
TTL = 1 if TTL_ENV == "auto" else int(TTL_ENV)


if not all([API_TOKEN, ZONE_ID, DNS_NAME]):
    raise ValueError("Missing one or more required environment variables: API_TOKEN, ZONE_ID, DNS_NAME.")

IP_PROVIDERS = {
    "ipify": "https://api.ipify.org?format=json",
    "icanhazip": "https://ipv4.icanhazip.com",
    "myip": "https://api.myip.com"
    
}

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def get_public_ip():
    if IP_PROVIDER not in IP_PROVIDERS:
        raise ValueError(f"Unsupported IP provider: {IP_PROVIDER}. Supported providers: {', '.join(IP_PROVIDERS.keys())}")

    try:
        response = requests.get(IP_PROVIDERS[IP_PROVIDER])
        response.raise_for_status()

        if "ip" in response.json():
            return response.json()["ip"]
        else:
            return response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch public IP from {IP_PROVIDER}: {e}")


async def get_dns_record():
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records?name={DNS_NAME}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    records = response.json()
    if records["success"] and records["result"]:
        return records["result"][0]
    return None

async def create_or_update_record(record=None):
    public_ip = get_public_ip()
    logger.info(f"Fetched public IP: {public_ip}")
    url = f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records"
    payload = {
        "type": "A",
        "name": DNS_NAME,
        "content": public_ip,
        "ttl": TTL,
        "proxied": PROXY
    }

    if record:
        record_id = record["id"]
        url = f"{url}/{record_id}"
        response = requests.put(url, headers=headers, json=payload)
    else:
        response = requests.post(url, headers=headers, json=payload)

    response.raise_for_status()
    return response.json()

async def manage_dns():
    try:
        logger.info("Starting DNS record update process...")
        existing_record = await get_dns_record()
        result = await create_or_update_record(existing_record)
        if result["success"]:
            action = "updated" if existing_record else "created"
            logger.info(f"DNS record successfully {action}. TTL: {TTL_ENV}, Proxied: {PROXY}")
        else:
            logger.error(f"Failed to update/create DNS record: {result['errors']}")
    except Exception as e:
        logger.error(f"Error during DNS management: {e}")

cron = aiocron.crontab(CRON_SCHEDULE, func=manage_dns, start=True)

if __name__ == "__main__":
    logger.info(f"DNS Manager started with provider '{IP_PROVIDER}'. Cron job scheduled with: {CRON_SCHEDULE}")
    logger.info(f"Proxy enabled: {PROXY}, TTL set to: {TTL_ENV}.")
    loop = asyncio.get_event_loop()
    loop.run_forever()
