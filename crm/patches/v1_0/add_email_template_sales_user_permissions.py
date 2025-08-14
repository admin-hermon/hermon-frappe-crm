import frappe


def execute():
    """Add Email Template permissions for Sales User and System Manager"""
    try:
        # Roles that should have full access to Email Template
        roles_to_add = [
            "Sales User",
            "System Manager",
        ]

        for role in roles_to_add:
            # Check if permission already exists
            if not frappe.db.exists(
                "Custom DocPerm", {"parent": "Email Template", "role": role}
            ):
                frappe.log(f"Adding {role} permissions to Email Template")

                perm_doc = frappe.get_doc(
                    {
                        "doctype": "Custom DocPerm",
                        "parent": "Email Template",
                        "parenttype": "DocType",
                        "parentfield": "permissions",
                        "role": role,
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
                    }
                )
                perm_doc.insert(ignore_permissions=True)

                frappe.log(f"Successfully added {role} permissions to Email Template")
            else:
                frappe.log(f"{role} permissions for Email Template already exist")

        # Clear cache after all permissions are added
        frappe.clear_cache(doctype="Email Template")
        frappe.log("Email Template permissions updated successfully")
    except Exception as e:
        frappe.log_error(f"Error adding Email Template permissions: {str(e)}")
