import logging

from aiohttp import web
from aiohttp.web_request import Request


class WhatsappBase(object):
    def __init__(self, *args, **kwargs):
        self.app = web.Application(*args, **kwargs)
        self.app.add_routes([
            web.get('/webhook', self.verify),
            web.post('/webhook', self.handle_message)
        ])
        self.config = {}

    async def verify(self, request: Request):
        mode = request.query.get("hub.mode")
        token = request.query.get("hub.verify_token")
        challenge = request.query.get("hub.challenge")
        # Check if a token and mode were sent
        if mode and token:
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
        web.run_app(self.app, *args, **kwargs)


if __name__ == '__main__':
    WhatsappBase().run()
