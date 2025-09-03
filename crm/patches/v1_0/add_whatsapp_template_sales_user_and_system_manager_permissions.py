import frappe

def execute():
    """
    Ensure WhatsApp Templates DocType permissions:
    - System Manager: full access (ownership)
    - Sales User: read/email/share only
    """
    try:
        doctype = "WhatsApp Templates"
        roles = {
            "System Manager": {
                "read": 1,
                "write": 1,
                "create": 1,
                "delete": 1,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
                "permlevel": 0,
                "if_owner": 0,
                "report": 1,
                "export": 1,
                "import": 1,
                "share": 1,
                "print": 1,
                "email": 1,
            },
            "Sales User": {
                "read": 1,
                "write": 0,
                "create": 0,
                "delete": 0,
                "submit": 0,
                "cancel": 0,
                "amend": 0,
                "permlevel": 0,
                "if_owner": 0,
                "report": 0,
                "export": 0,
                "import": 0,
                "share": 1,
                "print": 0,
                "email": 1,
            },
        }

        if not frappe.db.exists("DocType", doctype):
            frappe.log(f"{doctype} DocType does not exist. Skipping permission patch.")
            return

        for role, perms in roles.items():
            if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
                frappe.log(f"{role} permissions for {doctype} already exist. Skipping patch.")
                continue

            frappe.log(f"Adding {role} permissions to {doctype}")
            perm_doc = frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": doctype,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                **perms,
            })
            perm_doc.insert(ignore_permissions=True)
            frappe.log(f"Successfully added {role} permissions to {doctype}")

        frappe.clear_cache(doctype=doctype)
        frappe.log(f"{doctype} permissions updated successfully")
    except Exception as e:
        frappe.log_error(f"Error updating {doctype} permissions: {str(e)}")
