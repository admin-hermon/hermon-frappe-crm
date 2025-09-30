# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMNotification(Document):
	def on_update(self):
		if self.to_user:
			frappe.publish_realtime("crm_notification", user= self.to_user)

def notify_user(args):
	"""
	Notify the assigned user
	"""
	args = frappe._dict(args)
	if args.owner == args.assigned_to:
		return

	values = frappe._dict(
		doctype="CRM Notification",
		from_user=args.owner,
		to_user=args.assigned_to,
		type=args.notification_type,
		message=args.message,
		notification_text=args.notification_text,
		notification_type_doctype=args.reference_doctype,
		notification_type_doc=args.reference_docname,
		reference_doctype=args.redirect_to_doctype,
		reference_name=args.redirect_to_docname,
	)

	# Check for existing notifications to prevent duplicates using correct field mapping
	# Field usage reference for notification deduplication filter:
	# - reference_doctype: The DocType of the document the notification is about (e.g., "CRM Lead", "Communication").
	# - reference_name: The name (ID) of the document the notification is about (e.g., lead name, communication name).
	# - to_user: The user who should receive the notification.
	# - type: The type/category of notification (e.g., "Email", "SMS", "Mention").
	# These fields together uniquely identify a notification for a user about a specific document and type,
	# and are used to prevent duplicate notifications for the same event.
	if frappe.db.exists("CRM Notification", {
		"reference_doctype": values.reference_doctype,
		"reference_name": values.reference_name,
		"to_user": values.to_user,
		"type": values.type,
	}):
		return
	
	frappe.get_doc(values).insert(ignore_permissions=True)
