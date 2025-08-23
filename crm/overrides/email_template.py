import frappe
import re
from frappe import _
from frappe.email.doctype.email_template.email_template import EmailTemplate


class CustomEmailTemplate(EmailTemplate):
	"""
	Custom Email Template class that automatically makes attached files public.
	
	This override addresses the issue where images dragged into email templates
	are saved as private files, making them inaccessible to email recipients.
	
	Note: This only handles files uploaded via the rich text editor (drag & drop).
	If using raw HTML mode, users must manually ensure images use public URLs.
	"""
	
	def after_insert(self):
		"""
		Process files after template creation.
		
		Note: We use after_insert instead of before_save because:
		- In before_save, images are still base64 encoded
		- File processing happens during the save operation
		- after_insert ensures files exist as actual File documents
		"""
		self._make_template_files_public()
		
	def on_update(self):
		"""
		Process files after template updates.
		
		Handles cases where users add new images to existing templates.
		"""
		self._make_template_files_public()
	
	def _make_template_files_public(self):
		"""
		Automatically convert private files to public when used in email templates.
		
		This method:
		1. Finds all /private/files/ URLs in the template content
		2. Makes the corresponding File documents public (is_private = 0)
		3. Updates template content to use /files/ URLs instead
		
		Why we use frappe.db.set_value():
		- Calling self.save() in after_insert/on_update would create infinite loops
		- db.set_value() directly updates the database without triggering hooks
		- This is acceptable for post-processing cleanup operations
		
		Timing considerations:
		- Cannot use before_save: images are still base64 encoded
		- Must use after_insert/on_update: files exist as File documents
		- Files are processed after main save to avoid interference
		"""
		try:
			if not self.response:
				return

			# Example of a value in self.response: '<p>aaaaaa</p><img src="/private/files/gxGlukr.png?fid=cfc19137b7">'
			private_urls = re.findall(r'/private/files/([^/"\'>\s?]+(?:\.[^/"\'>\s?]+)?)', self.response)

			if not private_urls:
				return
			
			for filename in private_urls:
				file_doc = frappe.get_doc("File", {"file_name": filename})

				if file_doc.is_private:
					file_doc.is_private = 0
					file_doc.save()

			# Update template content to use public URLs - cover all occurences (all images)
			updated_response = re.sub(r'/private/files/', '/files/', self.response)

			if updated_response != self.response:
				# Use db.set_value to avoid triggering save hooks again
				# This prevents infinite loops while ensuring the change is persisted
				frappe.db.set_value("Email Template", self.name, "response", updated_response)
				self.response = updated_response
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Failed to change private files to public when saving the email template")

	@staticmethod
	def default_list_data():
		columns = [
			{
				'label': 'Name',
				'type': 'Data',
				'key': 'name',
				'width': '17rem',
			},
			{
				'label': 'Subject',
				'type': 'Data',
				'key': 'subject',
				'width': '12rem',
			},
			{
				'label': 'Enabled',
				'type': 'Check',
				'key': 'enabled',
				'width': '6rem',
			},
			{
				'label': 'Doctype',
				'type': 'Link',
				'key': 'reference_doctype',
				'width': '12rem',
			},
			{
				'label': 'Last Modified',
				'type': 'Datetime',
				'key': 'modified',
				'width': '8rem',
			},
		]
		rows = [
			"name",
			"enabled",
			"use_html",
			"reference_doctype",
			"subject",
			"response",
			"response_html",
			"modified",
		]
		return {'columns': columns, 'rows': rows}
