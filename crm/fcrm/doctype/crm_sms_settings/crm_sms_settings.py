import frappe
from frappe import _
from frappe.model.document import Document


class CRMSMSSettings(Document):
	def validate(self):
		# Ensure only one default messaging service
		if self.is_default:
			existing_default = frappe.db.get_value(
				"CRM SMS Settings", 
				{"is_default": 1, "name": ("!=", self.name)}, 
				"name"
			)
			if existing_default:
				frappe.throw(_("Another messaging service is already set as default. Please uncheck it first."))

	@classmethod
	def get_default_messaging_service_sid(cls):
		"""Get the default messaging service SID"""
		try:
			return frappe.db.get_value("CRM SMS Settings", {"is_default": 1}, "messaging_service_sid")
		except Exception:
			return None 