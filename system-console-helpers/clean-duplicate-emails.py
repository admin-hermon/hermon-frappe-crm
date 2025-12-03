"""
Paste this into the System Console on desk to find and remove duplicate emails (Communication doctypes).

Run this in case an Email Account sync error (IMAP pull) is causing duplicate emails to be created.

Dedup mechanism exists in frappe/email/receive.py
"""

def find_duplicates():
    """Find duplicate Communications by message_id"""
    print("Finding duplicate Communications...")
    
    # Find duplicate message_ids
    duplicates = frappe.db.sql("""
        SELECT 
            message_id,
            email_account,
            COUNT(*) as count,
            GROUP_CONCAT(name ORDER BY creation SEPARATOR ', ') as comm_names
        FROM `tabCommunication`
        WHERE message_id IS NOT NULL
            AND message_id != ''
            AND sent_or_received = 'Received'
            AND communication_type = 'Communication'
        GROUP BY message_id, email_account
        HAVING count > 1
    """, as_dict=True)
    
    print(f"Found {len(duplicates)} duplicate groups")
    
    # Get all duplicate Communication IDs to delete (keeping the first one)
    comms_to_delete = []
    comms_to_keep = []
    
    for dup in duplicates:
        comms = dup['comm_names'].split(', ')
        keep = comms[0]  # Keep the first (oldest)
        delete = comms[1:]  # Delete the rest
        
        comms_to_keep.append(keep)
        comms_to_delete.extend(delete)
    
    print(f"Total records to delete: {len(comms_to_delete)}")
    print(f"Communication IDs to delete: {', '.join(comms_to_delete)}")
    
    return comms_to_delete
    
def remove_duplicates(comm_ids):
    """Remove duplicate Communications"""
    print(f"Removing {len(comm_ids)} duplicate Communications...")
    
    deleted = 0
    errors = 0
    
    for comm_id in comm_ids:
        try:
            frappe.delete_doc("Communication", comm_id, force=1)
            print(f"Deleted: {comm_id}")
            deleted = deleted + 1
        except Exception as e:
            print(f"Error deleting {comm_id}: {str(e)}")
            errors = errors + 1

    frappe.db.commit()
    print(f"Deleted {deleted} records, {errors} errors")
    
comm_ids_to_delete = find_duplicates()
# remove_duplicates(comm_ids_to_delete)