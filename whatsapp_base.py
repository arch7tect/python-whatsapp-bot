import json
import logging
import os
import sys

import aiohttp
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

    async def handle_message(self, request: Request):
        try:
            body = await request.json()
            logging.debug("request body: %s", body)
            if (body.get("entry", [{}])[0]
                    .get("changes", [{}])[0]
                    .get("value", {})
                    .get("statuses")):
                logging.info("Received a WhatsApp status update.")
                return web.json_response({"status": "ok"}, status=200)
            if self.is_valid_whatsapp_message(body):
                await self.process_whatsapp_message(body)
                return web.json_response({"status": "ok"}, status=200)
            else:
                # if the request is not a WhatsApp API event, return an error
                return web.json_response({"status": "error", "message": "Not a WhatsApp API event"}, status=404)
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON")
            return web.json_response({"status": "error", "message": "Invalid JSON provided"}, status=400)

    def is_valid_whatsapp_message(self, body):
        """
        Check if the incoming webhook event has a valid WhatsApp message structure.
        """
        return (
                body.get("object")
                and body.get("entry")
                and body["entry"][0].get("changes")
                and body["entry"][0]["changes"][0].get("value")
                and body["entry"][0]["changes"][0]["value"].get("messages")
                and body["entry"][0]["changes"][0]["value"]["messages"][0]
        )

    async def process_whatsapp_message(self, body):
        wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
        name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

        message = body["entry"][0]["changes"][0]["value"]["messages"][0]
        message_body = message["text"]["body"]

        # TODO: implement custom function here
        response = await self.generate_response(message_body, wa_id, name)

        # OpenAI Integration
        # response = generate_response(message_body, wa_id, name)
        # response = process_text_for_whatsapp(response)

        data = self.get_text_message_input(self.config["RECIPIENT_WAID"], response)
        await self.send_message(data)

    async def generate_response(self, response_body, wa_id, name):
        # Return text in uppercase
        return f"{wa_id}/{name}: {response_body.upper()}"

    async def send_message(self, data):
        headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {self.config['ACCESS_TOKEN']}",
        }
        async with aiohttp.ClientSession() as session:
            url = f"https://graph.facebook.com/{self.config['VERSION']}/{self.config['PHONE_NUMBER_ID']}/messages"
            try:
                async with session.post(url, data=data, headers=headers) as response:
                    if response.status == 200:
                        print("Status:", response.status)
                        print("Content-type:", response.headers["content-type"])

                        html = await response.text()
                        print("Body:", html)
                    else:
                        print(response.status)
                        print(response)
            except aiohttp.ClientConnectorError as e:
                print("Connection Error", str(e))

    def get_text_message_input(self, recipient, text):
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            }
        )

    def run(self, *args, **kwargs):
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                            stream=sys.stdout,
                            )
        web.run_app(self.app, *args, **kwargs)


if __name__ == '__main__':
    WhatsappBase().run()
