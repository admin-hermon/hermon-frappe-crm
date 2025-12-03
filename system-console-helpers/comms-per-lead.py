"""
Paste this into the System Console on desk to find out stats about the Communication doctypes (emails)
"""
def count_communications_linked_to_leads():
    """Count Communications linked to CRM Leads"""
    
    # Total linked Communications
    total = frappe.db.count("Communication", {
        "reference_doctype": "CRM Lead",
        "reference_name": ["!=", ""]
    })
    
    # Unique Leads with Communications
    unique_leads = frappe.db.sql("""
        SELECT COUNT(DISTINCT reference_name)
        FROM `tabCommunication`
        WHERE reference_doctype = 'CRM Lead'
            AND reference_name IS NOT NULL
            AND reference_name != ''
    """)[0][0]
    
    # Breakdown by type
    breakdown = frappe.db.sql("""
        SELECT 
            sent_or_received,
            communication_type,
            COUNT(*) as count
        FROM `tabCommunication`
        WHERE reference_doctype = 'CRM Lead'
            AND reference_name IS NOT NULL
        GROUP BY sent_or_received, communication_type
    """, as_dict=True)
    
    print(f"Total Communications linked to Leads: {total}")
    print(f"Unique Leads with Communications: {unique_leads}")
    print("\nBreakdown:")
    for row in breakdown:
        print(f"{row.sent_or_received} - {row.communication_type}: {row.count}")
    
    return {
        "total": total,
        "unique_leads": unique_leads,
        "breakdown": breakdown
    }


count_communications_linked_to_leads()