import frappe
from frappe import _
from frappe.utils.password import get_decrypted_password
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VoiceGrant
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import Dial, VoiceResponse
from crm.api.doc import get_assigned_users

from .utils import get_public_url


class Twilio:
	"""Twilio connector over TwilioClient."""

	def __init__(self, settings):
		"""
		:param settings: `CRM Twilio Settings` doctype
		"""
		self.settings = settings
		self.account_sid = settings.account_sid
		self.application_sid = settings.twiml_sid
		self.api_key = settings.api_key
		self.api_secret = settings.get_password("api_secret")
		self.twilio_client = self.get_twilio_client()

	@classmethod
	def connect(self):
		"""Make a twilio connection."""
		settings = frappe.get_doc("CRM Twilio Settings")
		if not (settings and settings.enabled):
			return
		return Twilio(settings=settings)

	def get_phone_numbers(self):
		"""Get account's twilio phone numbers."""
		numbers = self.twilio_client.incoming_phone_numbers.list()
		return [n.phone_number for n in numbers]

	def generate_voice_access_token(self, identity: str, ttl=60 * 60):
		"""Generates a token required to make voice calls from the browser."""
		# identity is used by twilio to identify the user uniqueness at browser(or any endpoints).
		identity = self.safe_identity(identity)

		# Create access token with credentials
		token = AccessToken(self.account_sid, self.api_key, self.api_secret, identity=identity, ttl=ttl)

		# Create a Voice grant and add to token
		voice_grant = VoiceGrant(
			outgoing_application_sid=self.application_sid,
			incoming_allow=True,  # Allow incoming calls
		)
		token.add_grant(voice_grant)
		return token.to_jwt()

	@classmethod
	def safe_identity(cls, identity: str):
		"""Create a safe identity by replacing unsupported special charaters `@` with (at)).
		Twilio Client JS fails to make a call connection if identity has special characters like @, [, / etc)
		https://www.twilio.com/docs/voice/client/errors (#31105)
		"""
		return identity.replace("@", "(at)")

	@classmethod
	def emailid_from_identity(cls, identity: str):
		"""Convert safe identity string into emailID."""
		return identity.replace("(at)", "@")

	def get_recording_status_callback_url(self):
		url_path = "/api/method/crm.integrations.twilio.api.update_recording_info"
		return get_public_url(url_path)

	def get_update_call_status_callback_url(self):
		url_path = "/api/method/crm.integrations.twilio.api.update_call_status_info"
		return get_public_url(url_path)

	def generate_twilio_dial_response(self, from_number: str, to_number: str):
		"""Generates voice call instructions to forward the call to agents Phone."""
		resp = VoiceResponse()
		dial = Dial(
			caller_id=from_number,
			record=self.settings.record_calls,
			recording_status_callback=self.get_recording_status_callback_url(),
			recording_status_callback_event="completed",
		)
		dial.number(
			to_number,
			status_callback_event="initiated ringing answered completed",
			status_callback=self.get_update_call_status_callback_url(),
			status_callback_method="POST",
		)
		resp.append(dial)
		return resp

	def get_call_info(self, call_sid):
		return self.twilio_client.calls(call_sid).fetch()

	def generate_twilio_client_response(self, client, ring_tone="at"):
		"""Generates voice call instructions to forward the call to agents computer."""
		resp = VoiceResponse()
		dial = Dial(
			ring_tone=ring_tone,
			record=self.settings.record_calls,
			recording_status_callback=self.get_recording_status_callback_url(),
			recording_status_callback_event="completed",
		)
		dial.client(
			client,
			status_callback_event="initiated ringing answered completed",
			status_callback=self.get_update_call_status_callback_url(),
			status_callback_method="POST",
		)
		resp.append(dial)
		return resp

	@classmethod
	def get_twilio_client(self):
		twilio_settings = frappe.get_doc("CRM Twilio Settings")
		if not twilio_settings.enabled:
			frappe.throw(_("Please enable twilio settings before making a call."))

		auth_token = get_decrypted_password("CRM Twilio Settings", "CRM Twilio Settings", "auth_token")
		client = TwilioClient(twilio_settings.account_sid, auth_token)

		return client
	
	def send_sms(self, from_number: str, to_number: str, message: str) -> dict:
		twilio_message_create_response = self.twilio_client.messages.create(
			to=to_number,
			body=message,
			from_=from_number
		)

		return {
			'sid': twilio_message_create_response.sid,
			'message': twilio_message_create_response.body,
			'from_number': twilio_message_create_response.from_,
			'to_number': twilio_message_create_response.to,
			'status': twilio_message_create_response.status,
			'direction': 'Outgoing'
		}

class IncomingCall:
	def __init__(self, from_number, to_number, meta=None):
		self.from_number = from_number
		self.to_number = to_number
		self.meta = meta

	def process(self):
		"""Process the incoming call
		* Figure out who is going to pick the call (call attender)
		* Check call attender settings and forward the call to Phone
		"""
		twilio = Twilio.connect()
		attender = get_the_call_attender(self.from_number)

		if not attender:
			resp = VoiceResponse()
			resp.say(_("Agent is unavailable to take the call, please call after some time."))
			return resp

		return twilio.generate_twilio_client_response(twilio.safe_identity(attender))


def get_active_loggedin_users(users):
	"""Filter the current loggedin users from the given users list"""
	rows = frappe.db.sql(
		"""
		SELECT `user`
		FROM `tabSessions`
		WHERE `user` IN %(users)s
		""",
		{"users": users},
	)
	return [row[0] for row in set(rows)]


def get_the_call_attender(caller_number: str) -> str:
	"""
	Get the user name of the user most appropriate to take the incomming call based on lead assignees
	
	Note: In the original CRM implementation calls were tailored towards a 1 - 1 relationship between a user and a phone number
	via the Telephony Agent doctype and this method used to get the owner of a specific number

	Our usecase is more tailored towards a departmant of users sharing the entire frappe site instance and sharing a phone number / email address etc..
	"""
	# Find lead by caller number
	lead = frappe.db.get_value("CRM Lead", {"mobile_no": caller_number}, "name")
	if not lead:
		return None
	
	# Get lead assignees
	assignees = get_assigned_users("CRM Lead", lead)
	if not assignees:
		return None
	
	# Check which assignees are logged in
	logged_in_assignees = get_active_loggedin_users(assignees)
	if not logged_in_assignees:
		return None
	
	# Use first logged-in assignee
	return logged_in_assignees[0]


class TwilioCallDetails:
	def __init__(self, call_info, call_from=None, call_to=None):
		self.call_info = call_info
		self.account_sid = call_info.get("AccountSid")
		self.application_sid = call_info.get("ApplicationSid")
		self.call_sid = call_info.get("CallSid")
		self.call_status = self.get_call_status(call_info.get("CallStatus"))
		self._call_from = call_from or call_info.get("From")
		self._call_to = call_to or call_info.get("To")

	def get_direction(self):
		if self.call_info.get("Caller").lower().startswith("client"):
			return "Outgoing"
		return "Incoming"

	def get_from_number(self):
		return self._call_from or self.call_info.get("From")

	def get_to_number(self):
		return self._call_to or self.call_info.get("To")

	@classmethod
	def get_call_status(cls, twilio_status):
		"""Convert Twilio given status into system status."""
		twilio_status = twilio_status or ""
		return " ".join(twilio_status.split("-")).title()

	def to_dict(self):
		"""Convert call details into dict."""
		direction = self.get_direction()
		from_number = self.get_from_number()
		to_number = self.get_to_number()
		caller = ""
		receiver = ""

		if direction == "Outgoing":
			caller = self.call_info.get("Caller")
			identity = caller.replace("client:", "").strip()
			caller = Twilio.emailid_from_identity(identity) if identity else ""
		else:
			attender = get_the_call_attender(from_number)
			receiver = attender if attender else ""

		return {
			"type": direction,
			"status": self.call_status,
			"id": self.call_sid,
			"from": from_number,
			"to": to_number,
			"receiver": receiver,
			"caller": caller,
		}
