import logging
import os
import sys

from aiohttp import web
from aiohttp.web_request import Request
from dotenv import load_dotenv


class WhatsappBase(object):
    def __init__(self, *args, **kwargs):
        self.app = web.Application(*args, **kwargs)
        self.app.add_routes([
            web.get('/webhook', self.verify),
            web.post('/webhook', self.handle_message)
        ])
        self.config = {}
        load_dotenv()
        self.config["ACCESS_TOKEN"] = os.getenv("ACCESS_TOKEN")
        self.config["YOUR_PHONE_NUMBER"] = os.getenv("YOUR_PHONE_NUMBER")
        self.config["APP_ID"] = os.getenv("APP_ID")
        self.config["APP_SECRET"] = os.getenv("APP_SECRET")
        self.config["RECIPIENT_WAID"] = os.getenv("RECIPIENT_WAID")
        self.config["VERSION"] = os.getenv("VERSION")
        self.config["PHONE_NUMBER_ID"] = os.getenv("PHONE_NUMBER_ID")
        self.config["VERIFY_TOKEN"] = os.getenv("VERIFY_TOKEN")

    async def verify(self, request: Request):
        mode = request.query.get("hub.mode")
        token = request.query.get("hub.verify_token")
        challenge = request.query.get("hub.challenge")
        # Check if a token and mode were sent
        if mode and token and challenge:
            # Check the mode and token sent are correct
            if mode == "subscribe" and token == self.config["VERIFY_TOKEN"]:
                # Respond with 200 OK and challenge token from the request
                logging.info("WEBHOOK_VERIFIED")
                return web.Response(text=challenge, status=200)
            else:
                # Responds with '403 Forbidden' if verify tokens do not match
                logging.info("VERIFICATION_FAILED")
                return web.json_response({"status": "error", "message": "Verification failed"}, status=403)
        else:
            # Responds with '400 Bad Request' if verify tokens do not match
            logging.info("MISSING_PARAMETER")
            return web.json_response({"status": "error", "message": "Missing parameters"}, status=400)

    async def handle_message(self, request):
        return web.json_response({"text": "Hello, world"}, status=200)

    def run(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                            stream=sys.stdout,
                            )
        web.run_app(self.app, *args, **kwargs)


if __name__ == '__main__':
    WhatsappBase().run()
