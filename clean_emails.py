import sqlite3
import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Connect to database
conn = sqlite3.connect('emails.db')
c = conn.cursor()

# Get all emails
c.execute('SELECT email FROM emails')
emails = c.fetchall()

print("Before cleaning:")
for email in emails:
    print(f"  {email[0]}")

# Clean emails
valid_emails = []
for email_tuple in emails:
    email = email_tuple[0].strip()
    # Remove common suffixes that might be added
    email = re.sub(r'Enter.*$', '', email)
    email = re.sub(r'\.venv.*$', '', email)
    if validate_email(email):
        valid_emails.append(email)

# Clear table and insert clean emails
c.execute('DELETE FROM emails')
c.executemany('INSERT INTO emails (email) VALUES (?)', [(email,) for email in valid_emails])
conn.commit()

print("\nAfter cleaning:")
c.execute('SELECT email FROM emails')
clean_emails = c.fetchall()
for email in clean_emails:
    print(f"  {email[0]}")

print(f"\nCleaned {len(emails)} emails to {len(clean_emails)} valid emails")

conn.close()
