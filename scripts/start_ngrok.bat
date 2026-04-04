@echo off
REM Expose the MediScript backend to the internet for Twilio webhooks.
REM After running, copy the HTTPS forwarding URL and set it in the Twilio sandbox:
REM   Twilio Console -> Messaging -> Try it out -> Send a WhatsApp message
REM   Sandbox Configuration -> "WHEN A MESSAGE COMES IN":
REM     https://<random>.ngrok-free.app/api/twilio/webhook
ngrok http 8000 %*
