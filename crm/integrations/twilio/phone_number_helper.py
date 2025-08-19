import frappe

from phonenumbers import parse, is_valid_number, region_code_for_number, NumberParseException
from phonenumbers.geocoder import description_for_number
from phonenumbers.phonenumberutil import NumberParseException

from .twilio_handler import Twilio


def is_phone_number_valid(phone_number: str) -> bool:
    """
    Validate a phone number using the phonenumbers library https://pypi.org/project/phonenumbers/
    """
    try:
        parsed_phone_number = parse(phone_number, None)
        return is_valid_number(parsed_phone_number)
    except NumberParseException:
        return False


def analyze_phone_number(phone_number: str) -> dict:
    """
    Extract information from a phone number using the phonenumbers library https://pypi.org/project/phonenumbers/

    Args:
        phone_number: Phone number to analyze (e.g., "+14155551234")

    Returns:
        dict: {
            'geographic_description': 'San Francisco, CA', # Might return a country or a city - is the most specific description
            'country_code': 'US', # ISO country code (2 letter country code)
        }
    """

    parsed_phone_number = parse(phone_number, None)

    return {
        "geographic_description": description_for_number(
            parsed_phone_number, "en"
        ),  # Might return a country or a city - is the most specific description
        "country_code": region_code_for_number(
            parsed_phone_number
        ),  # ISO country code (2 letter country code)
    }


def get_from_number(caller: str, to_number: str) -> str:
    """
    Determine the optimal FROM number for a call or an SMS based on the caller agent and the destination number

    First tries to use a number from the pool of Twillion Number doctypes (if any) based on location and 
    falls back to using the user's telephony agent setting

    Args:
        caller: Caller identity (e.g., "client:user@example.com")
        to_number: Destination phone number

    Returns:
        FROM number to use for the call

    Raises:
        Exception: If no suitable number found
    """
    location_based_number = _get_number_based_on_location(to_number)

    if location_based_number:
        return location_based_number

    fallback_number = _get_telephony_agent_number(caller)

    if fallback_number:
        return fallback_number

    raise Exception(
        f"No suitable from number found for caller {caller} when communicating with {to_number}"
    )


def _get_number_based_on_location(to_number: str) -> str | None:
    """Find the best Twilio number by first matching the geographic description and then the country code"""
    try:
        to_number_details = analyze_phone_number(to_number)

        available_numbers = frappe.get_all(
            "CRM Twilio Number",
            filters={"enabled": 1},
            fields=[
                "phone_number",
                "geographic_description",
                "country_code",
            ],
        )

        if not available_numbers:
            return None

        geographic_description_map = {
            num.geographic_description: num.phone_number
            for num in available_numbers
            if num.geographic_description
        }

        from_number = geographic_description_map.get(
            to_number_details.get("geographic_description")
        )

        if from_number:
            return from_number

        country_code_map = {
            num.country_code: num.phone_number
            for num in available_numbers
            if num.country_code
        }

        from_number = country_code_map.get(to_number_details.get("country_code"))

        if from_number:
            return from_number

        return None
    except Exception as e:
        frappe.log_error(
            f"Error in geographic phone routing for {to_number}: {str(e)}",
            "Phone Routing",
        )
        return None


def _get_telephony_agent_number(caller: str) -> str | None:
    """Get telephony agent number for user (legacy fallback)"""
    try:
        identity = caller.replace("client:", "").strip()
        user = Twilio.emailid_from_identity(identity)
        return frappe.db.get_value("CRM Telephony Agent", user, "twilio_number")
    except Exception:
        return None
