import frappe


def execute():
    """Allow Sales User to edit Email Template"""
    try:
        # Check if permission already exists (important for safety)
        if not frappe.db.exists(
            "Custom DocPerm", {"parent": "Email Template", "role": "Sales User"}
        ):
            frappe.log("Adding Sales User permissions to Email Template")

            perm_doc = frappe.get_doc(
                {
                    "doctype": "Custom DocPerm",
                    "parent": "Email Template",
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": "Sales User",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 1,
                    "submit": 0,
                    "cancel": 0,
                    "amend": 0,
                    "permlevel": 0,
                    "if_owner": 0,
                }
            )
            perm_doc.insert(ignore_permissions=True)
            frappe.clear_cache(doctype="Email Template")

            frappe.log("Successfully added Sales User permissions to Email Template")
        else:
            frappe.log("Sales User permissions for Email Template already exist")

    except Exception as e:
        frappe.log_error(f"Error adding Email Template permissions: {str(e)}")
