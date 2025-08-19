from frappe import throw
from frappe.model.document import Document
from crm.integrations.twilio.phone_number_helper import (
    is_phone_number_valid,
    analyze_phone_number,
)


class CRMTwilioNumber(Document):
    def validate(self):
        """Validate phone number"""
        if not is_phone_number_valid(self.phone_number):
            throw("Invalid phone number")

    def before_save(self):
        """Auto-populate geographic information before saving"""
        if self.has_value_changed("phone_number"):
            self._populate_phone_analysis()

    def _populate_phone_analysis(self):
        """Populate all geographic and technical fields from phone number analysis"""
        phone_number_details = analyze_phone_number(self.phone_number)

        self.geographic_description = phone_number_details.get("geographic_description")
        self.country_code = phone_number_details.get("country_code")
