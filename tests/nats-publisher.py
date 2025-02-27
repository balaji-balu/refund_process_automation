import asyncio
import json
from nats.aio.client import Client as NATS

async def main():
    nc = NATS()
    await nc.connect("nats://localhost:4222")  # Change to the correct IP if needed

    message = {
        "user_id": 1,
        "order_id": 1,
        "reason": 1,
        "amount": 20
    }
    
    # Convert JSON to bytes and publish
    await nc.publish("updates", json.dumps(message).encode())
    #await nc.publish("updates", b"Hello from external publisher!")
    print("Message published!")

    await nc.close()

asyncio.run(main())
