import asyncio,yaml,sys
from amqtt.broker import Broker
async def main():
    b=Broker(yaml.safe_load(open('/home/claude/stack/relay/broker.yaml')));await b.start();print('broker up',flush=True)
    while True: await asyncio.sleep(3600)
asyncio.run(main())
