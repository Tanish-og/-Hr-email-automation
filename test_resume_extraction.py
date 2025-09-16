import PyPDF2
import re
import os

def extract_resume_text(pdf_path):
    """Extract text content from PDF resume"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
    except Exception as e:
        print(f"Error reading resume: {str(e)}")
        return ""

def extract_personal_info_from_resume(resume_text):
    """Extract personal information from resume text"""
    info = {
        'name': '',
        'email': '',
        'phone': '',
        'linkedin': '',
        'location': ''
    }

    if not resume_text:
        return info

    print("Resume text preview:")
    print(resume_text[:500] + "...")
    print("\n" + "="*50 + "\n")

    # Extract email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, resume_text)
    if emails:
        info['email'] = emails[0]
        print(f"✅ Found email: {emails[0]}")

    # Extract phone
    phone_pattern = r'\b\d{10}\b|\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, resume_text)
    if phones:
        info['phone'] = phones[0]
        print(f"✅ Found phone: {phones[0]}")

    # Extract LinkedIn
    linkedin_pattern = r'linkedin\.com/in/[\w-]+'
    linkedin_matches = re.findall(linkedin_pattern, resume_text, re.IGNORECASE)
    if linkedin_matches:
        info['linkedin'] = 'https://' + linkedin_matches[0]
        print(f"✅ Found LinkedIn: {info['linkedin']}")

    # Extract name (first line or prominent text)
    lines = resume_text.split('\n')[:5]
    print("Checking first 5 lines for name:")
    for i, line in enumerate(lines):
        print(f"Line {i+1}: '{line.strip()}'")
        line = line.strip()
        if line and len(line.split()) >= 2 and len(line) < 30:
            if not any(x in line.lower() for x in ['email', 'phone', 'address']):
                info['name'] = line
                print(f"✅ Selected name: {line}")
                break

    print(f"\n📋 Extracted Information:")
    print(f"Name: {info['name']}")
    print(f"Email: {info['email']}")
    print(f"Phone: {info['phone']}")
    print(f"LinkedIn: {info['linkedin']}")

    return info

if __name__ == "__main__":
    resume_path = "Tanish_resume_updated (1).pdf"

    if os.path.exists(resume_path):
        print(f"📄 Reading resume: {resume_path}")
        resume_text = extract_resume_text(resume_path)

        if resume_text:
            print(f"📝 Extracted {len(resume_text)} characters from resume")
            personal_info = extract_personal_info_from_resume(resume_text)
        else:
            print("❌ Could not extract text from resume")
    else:
        print(f"❌ Resume file not found: {resume_path}")
