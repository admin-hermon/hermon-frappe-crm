import frappe

def execute():
	"""
	Ensure the 'WhatsApp Manager' role has the necessary permissions to
	1. Read 'WhatsApp Templates' to select them in the UI.
	2. Create/Read/Write 'WhatsApp Message' to log sent messages.
	This patch handles cases where the frappe_whatsapp app's fixtures
	may not have been applied or are incomplete.
	"""
	if not frappe.db.exists("Role", "WhatsApp Manager"):
		frappe.log_info("WhatsApp Manager role not found, skipping patch.")
		return

	# Permissions to be ensured
	permissions_to_ensure = {
		"WhatsApp Templates": {"read": 1},
		"WhatsApp Message": {"read": 1, "write": 1, "create": 1},
	}

	for doctype, perms in permissions_to_ensure.items():
		if not frappe.db.exists("DocType", doctype):
			frappe.log_info(f"DocType '{doctype}' not found, skipping permissions.")
			continue

		# Using a dictionary for conditions
		base_conditions = {
			"role": "WhatsApp Manager",
			"parent": doctype,
		}

		# Check and grant each permission type individually
		for ptype, pvalue in perms.items():
			if pvalue == 1:
				conditions = base_conditions.copy()
				conditions[ptype] = 1
				if not frappe.db.exists("Custom DocPerm", conditions):
					perm_doc = frappe.get_doc({
						"doctype": "Custom DocPerm",
						"role": "WhatsApp Manager",
						"parent": doctype,
						"permlevel": 0,
					})
					perm_doc.set(ptype, 1)
					perm_doc.insert(ignore_permissions=True)
					frappe.log_info(f"Granted '{ptype}' permission on '{doctype}' to 'WhatsApp Manager'.")

	# We must clear the cache after changing permissions
	frappe.clear_cache(doctype="DocPerm")
