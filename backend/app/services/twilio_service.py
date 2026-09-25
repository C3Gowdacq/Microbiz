"""
backend/app/services/twilio_service.py

Twilio SMS & WhatsApp notification service for MicroBizAI.
Dispatches customer credit reminders, payment links, and purchase order alerts.
Supports both real Twilio dispatch (when credentials are in .env) and graceful
simulation fallback so the application never breaks if credentials are missing.
"""

import os
import re
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def format_phone_number(raw_phone: str) -> str:
    """
    Format a phone number into E.164 format (+91 for India by default).
    Example: '9876543210' -> '+919876543210'
    """
    if not raw_phone:
        return ""
    # Strip spaces, dashes, parentheses
    cleaned = re.sub(r"[\s\-\(\)]", "", str(raw_phone).strip())
    # If 10 digits without country code, assume India (+91)
    if re.fullmatch(r"\d{10}", cleaned):
        return f"+91{cleaned}"
    # If already starts with +, keep it
    if cleaned.startswith("+"):
        return cleaned
    # If starts with 91 followed by 10 digits
    if re.fullmatch(r"91\d{10}", cleaned):
        return f"+{cleaned}"
    return f"+{cleaned}"


def send_sms_or_whatsapp(
    to_phone: str,
    message_body: str,
    is_whatsapp: bool = False,
) -> Dict[str, Any]:
    """
    Send an SMS or WhatsApp message via Twilio.

    Reads configuration from environment variables:
      - TWILIO_ACCOUNT_SID
      - TWILIO_AUTH_TOKEN
      - TWILIO_PHONE_NUMBER       (e.g., '+12055550199')
      - TWILIO_WHATSAPP_NUMBER    (e.g., 'whatsapp:+14155238886')
      - DEMO_DEFAULT_CUSTOMER_PHONE (optional fallback test recipient)

    Returns:
      dict with keys: 'status' ('sent', 'simulated', 'error'), 'to', 'body', 'sid', 'detail'
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    auth_token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_PHONE_NUMBER", "").strip()
    whatsapp_from = os.getenv("TWILIO_WHATSAPP_NUMBER", "").strip()
    fallback_phone = os.getenv("DEMO_DEFAULT_CUSTOMER_PHONE", "").strip()

    target_phone = format_phone_number(to_phone or fallback_phone)

    if not target_phone:
        logger.warning("[TWILIO] No valid destination phone number provided.")
        return {
            "status": "error",
            "detail": "No destination phone number found for customer (and no DEMO_DEFAULT_CUSTOMER_PHONE fallback set).",
            "to": to_phone,
            "body": message_body,
        }

    # If credentials are not provided in .env, operate in simulation mode
    if not account_sid or not auth_token:
        logger.info(
            f"[TWILIO SIMULATION] Account credentials not set in .env. "
            f"Simulating {'WhatsApp' if is_whatsapp else 'SMS'} to {target_phone}: \"{message_body}\""
        )
        return {
            "status": "simulated",
            "detail": "Twilio credentials not configured in .env. Message recorded in system audit trail.",
            "to": target_phone,
            "body": message_body,
            "simulated": True,
        }

    try:
        from twilio.rest import Client

        # Handle API Key (SK...) vs Account SID (AC...)
        main_account_sid = os.getenv("TWILIO_MAIN_ACCOUNT_SID", "").strip() or os.getenv("TWILIO_ACCOUNT_SID_AC", "").strip()
        if account_sid.startswith("SK"):
            if main_account_sid and main_account_sid.startswith("AC"):
                client = Client(account_sid, auth_token, main_account_sid)
            else:
                err_msg = (
                    "TWILIO_ACCOUNT_SID in .env starts with 'SK', which is an API Key SID. "
                    "Twilio requires your main Account SID (starts with 'AC...') found on your "
                    "Twilio Console dashboard (https://console.twilio.com). "
                    "Either replace TWILIO_ACCOUNT_SID with your 'AC...' SID, or set TWILIO_MAIN_ACCOUNT_SID=AC..."
                )
                logger.error(f"[TWILIO ERROR] {err_msg}")
                return {
                    "status": "error",
                    "detail": err_msg,
                    "to": target_phone,
                    "body": message_body,
                }
        else:
            client = Client(account_sid, auth_token)

        # Check From number
        clean_from = format_phone_number(from_number) if not is_whatsapp else (whatsapp_from or "whatsapp:+14155238886")
        if not is_whatsapp and clean_from == target_phone:
            err_msg = (
                f"TWILIO_PHONE_NUMBER in .env is set to '{from_number}', which is the destination customer phone! "
                "In Twilio, 'From' must be the Twilio virtual number (e.g. +1...) provided in your Twilio Console."
            )
            logger.error(f"[TWILIO ERROR] {err_msg}")
            return {
                "status": "error",
                "detail": err_msg,
                "to": target_phone,
                "body": message_body,
            }

        if is_whatsapp and whatsapp_from:
            wa_to = f"whatsapp:{target_phone}" if not target_phone.startswith("whatsapp:") else target_phone
            wa_from = f"whatsapp:{whatsapp_from}" if not whatsapp_from.startswith("whatsapp:") else whatsapp_from
            msg = client.messages.create(
                body=message_body,
                from_=wa_from,
                to=wa_to,
            )
        else:
            if not from_number:
                return {
                    "status": "error",
                    "detail": "TWILIO_PHONE_NUMBER not configured in .env",
                    "to": target_phone,
                    "body": message_body,
                }
            msg = client.messages.create(
                body=message_body,
                from_=from_number,
                to=target_phone,
            )

        logger.info(f"[TWILIO SUCCESS] Message SID {msg.sid} dispatched to {target_phone}")
        return {
            "status": "sent",
            "sid": msg.sid,
            "to": target_phone,
            "body": message_body,
            "simulated": False,
        }

    except Exception as exc:
        err_msg = str(exc)
        logger.error(f"[TWILIO ERROR] Failed to send message to {target_phone}: {err_msg}")
        return {
            "status": "error",
            "detail": err_msg,
            "to": target_phone,
            "body": message_body,
        }
