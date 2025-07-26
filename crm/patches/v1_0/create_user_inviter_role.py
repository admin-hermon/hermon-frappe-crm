import frappe

def execute():
    """Create the User Inviter role if it doesn't exist"""
    
    role_name = "User Inviter"
    
    # Check if role already exists
    if frappe.db.exists("Role", role_name):
        return
    
    # Create the role
    role_doc = frappe.get_doc({
        "doctype": "Role",
        "role_name": role_name,
        "description": "Role for users who can invite new members but have limited access to other settings"
    })
    
    role_doc.insert(ignore_permissions=True)
    frappe.db.commit()
