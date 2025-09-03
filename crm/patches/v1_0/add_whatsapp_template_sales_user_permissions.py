import frappe

def execute():
    """
    Add WhatsApp Templates read/email/share permissions for Sales User.

    Note:
    - This patch does NOT override or remove base DocType permissions for other roles (e.g., System Manager).
    - Only roles with Custom DocPerms will appear in the Role Permission Manager for this DocType.
    - Base permissions for other roles remain intact and effective unless a Custom DocPerm is added for them.
    """
    try:
        role = "Sales User"
        doctype = "WhatsApp Templates"

        if not frappe.db.exists("DocType", doctype):
            frappe.log(f"{doctype} DocType does not exist. Skipping permission patch.")
            return

        if frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": role}):
            frappe.log(f"{role} permissions for {doctype} already exist. Skipping patch.")
            return

        frappe.log(f"Adding {role} permissions to {doctype}")

        perm_doc = frappe.get_doc(
            {
                "doctype": "Custom DocPerm",
                "parent": doctype,
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "read": 1,
                "email": 1,
                "share": 1,
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
                "print": 0,
            }
        )

        perm_doc.insert(ignore_permissions=True)
        frappe.clear_cache(doctype=doctype)

        frappe.log(f"Successfully added {role} permissions to {doctype}")
    except Exception as e:
        frappe.log_error(f"Error adding {doctype} permissions: {str(e)}")
