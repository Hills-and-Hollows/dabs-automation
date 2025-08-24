I checked the capabilities of the Gmail and Google Calendar connectors currently enabled for you. They provide read‑only operations (searching and reading emails and events), but they do **not** allow sending mail or creating new calendar events. I verified this by inspecting the API documentation and available endpoints; there are only functions like `get_profile`, `read_email`, `search_emails` for Gmail and `search_events`, `read_event` for Google Calendar.

Because of these limitations, we can’t programmatically send notification emails or automatically create calendar reminders through the connectors. Instead, here’s how you can integrate notifications with the automation workflow:

1. **Email notifications via Python** – Augment your existing automation script to send an email when a new NAXML file is generated. You can do this using Python’s built‑in `smtplib` module or a transactional email service. For example:

   ```python
   import smtplib
   from email.message import EmailMessage

   def send_notification(path_to_xml, recipients):
       msg = EmailMessage()
       msg['Subject'] = 'DABS Price Update Generated'
       msg['From'] = 'shawn@owenent.com'  # Replace with your own email address
       msg['To'] = ', '.join(recipients)  # List of recipient email addresses
       msg.set_content('This is a test email message.')
       with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
           smtp.login('your_email_address', 'your_app_password')  # Replace with your Gmail credentials
           smtp.send_message(msg)
   ```

   You would call `send_notification()` at the end of your `dabs_automation.py` script, passing in the path to the generated XML and a list of recipients (e.g., Tessa’s and Heather’s email addresses).

2. **Manual Google Calendar reminders** – Until create/write access is available through the connector, set up recurring events in Google Calendar by hand. Create a monthly event on the day you usually run the DABS price update (e.g., the 25th of each month) and add email or pop‑up reminders to notify you in advance. This will ensure you’re prompted to download the latest price list and run the automation script.

3. **Monitoring with the API** – You can still use the Google Calendar API’s `search_events` endpoint to confirm that reminders are on the calendar. For example, searching for upcoming events containing “DABS” between two dates returns an empty result set, indicating no events currently exist. Once you’ve created the calendar reminder manually, you can periodically query it to ensure it’s scheduled correctly.

To recap: because the current Gmail and Calendar connectors don’t support sending or creating, notifications must be handled outside the connector system—for example via SMTP emails sent from your automation script and manual calendar entries. This approach will still give Tessa and Heather timely alerts about price updates while keeping the automation workflow intact. If write‑capable APIs become available in the future, we can revisit automating these notifications fully.
