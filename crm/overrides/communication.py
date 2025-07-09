import frappe
from frappe import _

from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user


def on_update(doc, method):
	"""
	This function is hooked to the 'on_update' event of the 'Communication' doctype.
	It inspects the communication medium and calls the appropriate handler.
	"""
	# Map of communication mediums to their specific notification handlers.
	# This makes it easy to add new communication channels in the future.
	handler_map = {
		"Email": _handle_incoming_email,
	}

	handler = handler_map.get(doc.communication_medium)

	if handler:
		handler(doc)


def _handle_incoming_email(doc):
	"""Create a notification when an email is received and linked to a Lead."""
	try:
		if doc.sent_or_received != "Received":
			return

		if doc.reference_doctype != "CRM Lead":
			return

		if not doc.reference_name:
			return

		notification_text = f"""
			<div class="mb-2 leading-5 text-ink-gray-5">
				<span class="font-medium text-ink-gray-9">{ _('You') }</span>
				<span>{ _('received an email in lead') }</span>
				<span class="font-medium text-ink-gray-9">{ doc.reference_name }</span>
			</div>
		"""

		assigned_users = get_assigned_users(doc.reference_doctype, doc.reference_name)

		for user in assigned_users:
			notify_user(
				{
					"owner": doc.owner,
					"assigned_to": user,
					"notification_type": "Email",
					"message": doc.content,
					"notification_text": notification_text,
					"reference_doctype": "Communication",
					"reference_docname": doc.name,
					"redirect_to_doctype": doc.reference_doctype,
					"redirect_to_docname": doc.reference_name,
				}
			)
	except Exception:
		# Log the error for administrators to review, but don't block the user's action.
		frappe.log_error(frappe.get_traceback(), "Email Notification Failed")
