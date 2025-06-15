import json

import frappe
from frappe import _
from werkzeug.wrappers import Response

from crm.integrations.api import get_contact_by_phone_number

from .twilio_handler import IncomingCall, Twilio, TwilioCallDetails


@frappe.whitelist()
def is_enabled():
	return frappe.db.get_single_value("CRM Twilio Settings", "enabled")


@frappe.whitelist()
def generate_access_token():
	twilio = Twilio.connect()
	if not twilio:
		return {}

	from_number = frappe.db.get_value("CRM Telephony Agent", frappe.session.user, "twilio_number")
	if not from_number:
		return {
			"ok": False,
			"error": "caller_phone_identity_missing",
			"detail": "Phone number is not mapped to the caller",
		}

	token = twilio.generate_voice_access_token(identity=frappe.session.user)
	return {"token": token}  # ✅ already a string


@frappe.whitelist(allow_guest=True)
def voice(**kwargs):
	"""This is a webhook called by twilio to get instructions when the voice call request comes to twilio server."""

	def _get_caller_number(caller):
		identity = caller.replace("client:", "").strip()
		user = Twilio.emailid_from_identity(identity)
		return frappe.db.get_value("CRM Telephony Agent", user, "twilio_number")

	args = frappe._dict(kwargs)
	twilio = Twilio.connect()
	if not twilio:
		return

	assert args.AccountSid == twilio.account_sid
	assert args.ApplicationSid == twilio.application_sid

	# Generate TwiML instructions to make a call
	from_number = _get_caller_number(args.Caller)
	resp = twilio.generate_twilio_dial_response(from_number, args.To)

	call_details = TwilioCallDetails(args, call_from=from_number)
	create_call_log(call_details)
	return Response(resp.to_xml(), mimetype="text/xml")


@frappe.whitelist(allow_guest=True)
def twilio_incoming_call_handler(**kwargs):
	args = frappe._dict(kwargs)
	call_details = TwilioCallDetails(args)
	create_call_log(call_details)

	resp = IncomingCall(args.From, args.To).process()
	return Response(resp.to_xml(), mimetype="text/xml")


def create_call_log(call_details: TwilioCallDetails):
	details = call_details.to_dict()

	call_log = frappe.get_doc({**details, "doctype": "CRM Call Log", "telephony_medium": "Twilio"})

	# link call log with lead/deal
	contact_number = details.get("from") if details.get("type") == "Incoming" else details.get("to")
	link(contact_number, call_log)

	call_log.save(ignore_permissions=True)
	frappe.db.commit()
	return call_log


def link(contact_number, call_log):
	contact = get_contact_by_phone_number(contact_number)
	if contact.get("name"):
		doctype = "Contact"
		docname = contact.get("name")
		if contact.get("lead"):
			doctype = "CRM Lead"
			docname = contact.get("lead")
		elif contact.get("deal"):
			doctype = "CRM Deal"
			docname = contact.get("deal")
		call_log.link_with_reference_doc(doctype, docname)


def update_call_log(call_sid, status=None):
	"""Update call log status."""
	twilio = Twilio.connect()
	if not (twilio and frappe.db.exists("CRM Call Log", call_sid)):
		return

	try:
		call_details = twilio.get_call_info(call_sid)
		call_log = frappe.get_doc("CRM Call Log", call_sid)
		call_log.status = TwilioCallDetails.get_call_status(status or call_details.status)
		call_log.duration = call_details.duration
		call_log.start_time = get_datetime_from_timestamp(call_details.start_time)
		call_log.end_time = get_datetime_from_timestamp(call_details.end_time)
		call_log.save(ignore_permissions=True)
		frappe.db.commit()
		return call_log
	except Exception:
		frappe.log_error(title="Error while updating call record")
		frappe.db.commit()


@frappe.whitelist(allow_guest=True)
def update_recording_info(**kwargs):
	try:
		args = frappe._dict(kwargs)
		recording_url = args.RecordingUrl
		call_sid = args.CallSid
		update_call_log(call_sid)
		frappe.db.set_value("CRM Call Log", call_sid, "recording_url", recording_url)
	except Exception:
		frappe.log_error(title=_("Failed to capture Twilio recording"))


@frappe.whitelist(allow_guest=True)
def update_call_status_info(**kwargs):
	try:
		args = frappe._dict(kwargs)
		parent_call_sid = args.ParentCallSid
		update_call_log(parent_call_sid, status=args.CallStatus)

		call_info = {
			"ParentCallSid": args.ParentCallSid,
			"CallSid": args.CallSid,
			"CallStatus": args.CallStatus,
			"CallDuration": args.CallDuration,
			"From": args.From,
			"To": args.To,
		}

		client = Twilio.get_twilio_client()
		client.calls(args.ParentCallSid).user_defined_messages.create(content=json.dumps(call_info))
	except Exception:
		frappe.log_error(title=_("Failed to update Twilio call status"))


def get_datetime_from_timestamp(timestamp):
	from datetime import datetime
	from zoneinfo import ZoneInfo

	if not timestamp:
		return None

	datetime_utc_tz_str = timestamp.strftime("%Y-%m-%d %H:%M:%S%z")
	datetime_utc_tz = datetime.strptime(datetime_utc_tz_str, "%Y-%m-%d %H:%M:%S%z")
	system_timezone = frappe.utils.get_system_timezone()
	converted_datetime = datetime_utc_tz.astimezone(ZoneInfo(system_timezone))
	return frappe.utils.format_datetime(converted_datetime, "yyyy-MM-dd HH:mm:ss")


@frappe.whitelist()
def get_sms_history(lead_identifier: str) -> list:
	"""Get SMS history for a lead"""
	if not frappe.db.exists("CRM Lead", lead_identifier):
		frappe.throw(_("You must provide a valid lead to get SMS history"))

	return frappe.get_all(
		'SMS Message',
		filters={'lead': lead_identifier},
		fields=['name', 'direction', 'from_number', 'to_number', 'message', 'status', 'creation'],
		order_by='creation desc'
	)


@frappe.whitelist()
def send_sms(lead_identifier: str, message: str):
	lead_doc = frappe.get_doc('CRM Lead', lead_identifier)

	if not lead_doc:
		frappe.throw(_("Lead not found"))

	if not lead_doc.mobile_no:
		frappe.throw(_("No mobile number found for this lead"))

	twilio = Twilio.connect()
	sent_message = twilio.send_sms(lead_doc.mobile_no, message)

	sms = frappe.new_doc('SMS Message')
	sms.lead = lead_doc.name
	sms.direction = sent_message.get('direction')
	sms.from_number = sent_message.get('from_number')
	sms.to_number = sent_message.get('to_number')
	sms.message = sent_message.get('message')
	sms.twilio_sid = sent_message.get('sid')
	sms.status = sent_message.get('status')
	sms.insert()


@frappe.whitelist(allow_guest=True)
def handle_incoming_sms(**kwargs):
	webhook_data = frappe._dict(kwargs)

	from_number = webhook_data.get('From')
	to_number = webhook_data.get('To')
	message_body = webhook_data.get('Body')
	message_sid = webhook_data.get('MessageSid')
	status = webhook_data.get('SmsStatus')

	lead_name = frappe.db.get_value(
		"CRM Lead", {"mobile_no": from_number}, "name"
	)

	sms = frappe.new_doc('SMS Message')
	sms.lead = lead_name
	sms.direction = 'Incoming'
	sms.from_number = from_number
	sms.to_number = to_number
	sms.message = message_body
	sms.twilio_sid = message_sid
	sms.status = status
	sms.insert(ignore_permissions=True)
