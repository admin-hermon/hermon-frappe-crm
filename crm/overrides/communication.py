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
		"Email": _notify_about_incoming_email,
	}

	handler = handler_map.get(doc.communication_medium)

	if handler:
		handler(doc)


def _notify_about_incoming_email(doc):
	"""
	Create a notification when an email is received and linked to a Lead.
	
	Communication Flow & Deduplication Logic:
	========================================
	
	When an email arrives, Frappe processes it in multiple steps:
	1. Email arrives → Communication document created (basic info, no lead reference)
	2. Email processing → Communication updated with lead reference (reference_doctype, reference_name)
	3. Content processing → Communication updated with processed content/timeline links
	
	Each update triggers the on_update hook, potentially creating duplicate notifications.
	
	How has_value_changed() Works:
	=============================
	
	has_value_changed(fieldname) is a Frappe Document method that:
	- Compares current field value with the value before the current save operation
	- Returns True if the field value changed during this save
	- Returns False if the field value remained the same
	- Only works during document lifecycle events (validate, before_save, on_update, etc.)
	
	Example:
	- Initial: reference_doctype = None
	- Update 1: reference_doctype = "CRM Lead" → has_value_changed("reference_doctype") = True
	- Update 2: reference_doctype = "CRM Lead" → has_value_changed("reference_doctype") = False
	
	Why This Deduplication Works:
	============================
	
	We only send notifications when reference fields change (email gets linked to lead):
	- First on_update: reference_doctype changes from None → "CRM Lead" → Notification sent ✓
	- Second on_update: only content/timeline changes → No reference field changes → No notification ✓
	
	This ensures exactly one notification per email-to-lead linking event.
	"""
	try:
		if doc.sent_or_received != "Received":
			return

		if doc.reference_doctype != "CRM Lead":
			return

		if not doc.reference_name:
			return
		
		# Only notify when email is first linked to a lead (not on content updates)
		if not (doc.has_value_changed("reference_doctype") or doc.has_value_changed("reference_name")):
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
		frappe.log_error(frappe.get_traceback(), "Creating a notification for an incomming Email failed")
