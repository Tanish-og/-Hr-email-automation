"""
LinkedIn Job Scraper for AI/ML Engineer Positions
Automatically finds job openings and sends hiring emails to HR contacts
"""

import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv
import sqlite3

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobPosting:
    """Data class for job posting information"""
    title: str
    company: str
    location: str
    job_url: str
    company_url: str
    description: str
    posted_date: str
    hr_emails: List[str] = None

    def __post_init__(self):
        if self.hr_emails is None:
            self.hr_emails = []

class LinkedInJobScraper:
    """LinkedIn job scraper for AI/ML positions"""

    def __init__(self):
        self.jobs_db = 'linkedin_jobs.db'
        self.setup_database()
        self.driver = None
        self.wait_time = 3

    def setup_database(self):
        """Set up SQLite database for storing job postings"""
        conn = sqlite3.connect(self.jobs_db)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            job_url TEXT UNIQUE,
            company_url TEXT,
            description TEXT,
            posted_date TEXT,
            hr_emails TEXT,
            processed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.commit()
        conn.close()

    def init_driver(self):
        """Initialize Chrome WebDriver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Add user agent to avoid detection
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def search_linkedin_jobs(self, keywords: str = "AI ML engineer", location: str = "India", max_jobs: int = 50) -> List[JobPosting]:
        """Search for jobs on LinkedIn"""
        if not self.driver:
            self.init_driver()

        jobs = []
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location}"

        try:
            logger.info(f"Searching LinkedIn for: {keywords} in {location}")
            self.driver.get(search_url)

            # Wait for page to load
            time.sleep(self.wait_time)

            # Scroll to load more jobs
            for _ in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            # Find job cards
            job_cards = self.driver.find_elements(By.CLASS_NAME, "job-search-card")

            logger.info(f"Found {len(job_cards)} job cards")

            for card in job_cards[:max_jobs]:
                try:
                    # Extract job information
                    title_elem = card.find_element(By.CLASS_NAME, "job-search-card__title")
                    company_elem = card.find_element(By.CLASS_NAME, "job-search-card__company-name")
                    location_elem = card.find_element(By.CLASS_NAME, "job-search-card__location")
                    link_elem = card.find_element(By.TAG_NAME, "a")

                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    location_text = location_elem.text.strip()
                    job_url = link_elem.get_attribute("href")

                    # Extract company URL from job URL
                    company_url = self.extract_company_url(job_url)

                    job = JobPosting(
                        title=title,
                        company=company,
                        location=location_text,
                        job_url=job_url,
                        company_url=company_url,
                        description="",
                        posted_date=""
                    )

                    jobs.append(job)
                    logger.info(f"Extracted job: {title} at {company}")

                except Exception as e:
                    logger.warning(f"Error extracting job card: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching LinkedIn jobs: {e}")

        return jobs

    def extract_company_url(self, job_url: str) -> str:
        """Extract company LinkedIn URL from job URL"""
        try:
            # LinkedIn job URLs typically contain company info
            if 'company' in job_url:
                parts = job_url.split('/company/')
                if len(parts) > 1:
                    company_slug = parts[1].split('/')[0]
                    return f"https://www.linkedin.com/company/{company_slug}"
        except:
            pass
        return ""

    def get_job_description(self, job_url: str) -> str:
        """Get detailed job description from job URL"""
        if not self.driver:
            self.init_driver()

        try:
            self.driver.get(job_url)
            time.sleep(2)

            # Find job description
            desc_elements = self.driver.find_elements(By.CLASS_NAME, "jobs-description-content__text")
            if desc_elements:
                return desc_elements[0].text.strip()

            # Alternative selectors
            desc_selectors = [
                "jobs-description-content__text",
                "job-description",
                "description"
            ]

            for selector in desc_selectors:
                try:
                    desc_elem = self.driver.find_element(By.CLASS_NAME, selector)
                    return desc_elem.text.strip()
                except:
                    continue

        except Exception as e:
            logger.warning(f"Error getting job description: {e}")

        return ""

    def find_company_hr_emails(self, company_name: str, company_url: str = "") -> List[str]:
        """Find HR email addresses for a company"""
        emails = []

        # Method 1: Search company website
        if company_url:
            company_website = self.get_company_website_from_linkedin(company_url)
            if company_website:
                emails.extend(self.scrape_website_for_emails(company_website, ["hr", "careers", "jobs"]))

        # Method 2: Generate common HR email patterns
        domain = self.extract_domain_from_company(company_name)
        if domain:
            common_patterns = [
                f"hr@{domain}",
                f"careers@{domain}",
                f"jobs@{domain}",
                f"recruitment@{domain}",
                f"talent@{domain}",
                f"hiring@{domain}",
                f"recruit@{domain}"
            ]
            emails.extend(common_patterns)

        # Method 3: Search Google for company HR emails
        google_emails = self.search_google_for_hr_emails(company_name)
        emails.extend(google_emails)

        # Remove duplicates and validate
        validated_emails = []
        seen = set()
        for email in emails:
            if email not in seen and self.validate_email_format(email):
                validated_emails.append(email)
                seen.add(email)

        return validated_emails[:5]  # Limit to 5 emails per company

    def get_company_website_from_linkedin(self, company_url: str) -> str:
        """Extract company website from LinkedIn company page"""
        if not self.driver:
            self.init_driver()

        try:
            self.driver.get(company_url)
            time.sleep(2)

            # Look for website link
            website_selectors = [
                "a[href*='http'][href*='://']",
                ".company-details-panel__website",
                ".org-top-card-summary__website"
            ]

            for selector in website_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute("href")
                        if href and 'linkedin.com' not in href and 'http' in href:
                            return href
                except:
                    continue

        except Exception as e:
            logger.warning(f"Error getting company website: {e}")

        return ""

    def scrape_website_for_emails(self, website_url: str, keywords: List[str] = None) -> List[str]:
        """Scrape website for email addresses"""
        emails = []

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(website_url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find emails in text
            text = soup.get_text()
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            found_emails = re.findall(email_pattern, text)

            # Filter by keywords if provided
            if keywords:
                filtered_emails = []
                for email in found_emails:
                    email_lower = email.lower()
                    if any(keyword.lower() in email_lower for keyword in keywords):
                        filtered_emails.append(email)
                found_emails = filtered_emails

            emails.extend(found_emails)

            # Also check mailto links
            mailto_links = soup.find_all('a', href=re.compile(r'mailto:'))
            for link in mailto_links:
                email = link['href'].replace('mailto:', '')
                if self.validate_email_format(email):
                    emails.append(email)

        except Exception as e:
            logger.warning(f"Error scraping website {website_url}: {e}")

        return list(set(emails))  # Remove duplicates

    def search_google_for_hr_emails(self, company_name: str) -> List[str]:
        """Search Google for company HR email addresses"""
        emails = []

        try:
            query = f'"{company_name}" HR email site:linkedin.com OR site:indeed.com OR site:glassdoor.com'
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }

            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract emails from search results
            text = soup.get_text()
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            found_emails = re.findall(email_pattern, text)

            emails.extend(found_emails)

        except Exception as e:
            logger.warning(f"Error searching Google for {company_name}: {e}")

        return list(set(emails))

    def extract_domain_from_company(self, company_name: str) -> str:
        """Extract domain from company name"""
        # Clean company name
        clean_name = re.sub(r'[^\w\s]', '', company_name.lower())
        clean_name = clean_name.replace(' ', '')

        # Common domain patterns
        if clean_name:
            return f"{clean_name}.com"

        return ""

    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def save_jobs_to_db(self, jobs: List[JobPosting]):
        """Save job postings to database"""
        conn = sqlite3.connect(self.jobs_db)
        c = conn.cursor()

        for job in jobs:
            try:
                hr_emails_json = json.dumps(job.hr_emails)
                c.execute('''INSERT OR REPLACE INTO jobs
                    (title, company, location, job_url, company_url, description, posted_date, hr_emails)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (job.title, job.company, job.location, job.job_url,
                     job.company_url, job.description, job.posted_date, hr_emails_json))
            except Exception as e:
                logger.error(f"Error saving job {job.title}: {e}")

        conn.commit()
        conn.close()
        logger.info(f"Saved {len(jobs)} jobs to database")

    def load_unprocessed_jobs(self) -> List[JobPosting]:
        """Load unprocessed jobs from database"""
        conn = sqlite3.connect(self.jobs_db)
        c = conn.cursor()

        c.execute('SELECT * FROM jobs WHERE processed = 0')
        rows = c.fetchall()

        jobs = []
        for row in rows:
            hr_emails = json.loads(row[8]) if row[8] else []
            job = JobPosting(
                title=row[1],
                company=row[2],
                location=row[3],
                job_url=row[4],
                company_url=row[5],
                description=row[6],
                posted_date=row[7],
                hr_emails=hr_emails
            )
            jobs.append(job)

        conn.close()
        return jobs

    def mark_job_processed(self, job_url: str):
        """Mark job as processed"""
        conn = sqlite3.connect(self.jobs_db)
        c = conn.cursor()
        c.execute('UPDATE jobs SET processed = 1 WHERE job_url = ?', (job_url,))
        conn.commit()
        conn.close()

    def run_full_pipeline(self):
        """Run the complete LinkedIn job scraping and HR email finding pipeline"""
        logger.info("Starting LinkedIn job scraping pipeline...")

        # Step 1: Search for AI/ML jobs
        jobs = self.search_linkedin_jobs("AI ML engineer", "India", 20)
        logger.info(f"Found {len(jobs)} AI/ML jobs")

        # Step 2: Get detailed job descriptions
        for job in jobs:
            if not job.description:
                job.description = self.get_job_description(job.job_url)
                time.sleep(1)  # Rate limiting

        # Step 3: Find HR emails for each company
        for job in jobs:
            if not job.hr_emails:
                logger.info(f"Finding HR emails for {job.company}")
                job.hr_emails = self.find_company_hr_emails(job.company, job.company_url)
                time.sleep(2)  # Rate limiting

        # Step 4: Save to database
        self.save_jobs_to_db(jobs)

        # Step 5: Close browser
        if self.driver:
            self.driver.quit()

        logger.info("Pipeline completed successfully!")
        return jobs

def main():
    """Main function to run the LinkedIn scraper"""
    scraper = LinkedInJobScraper()

    print("LinkedIn AI/ML Job Scraper")
    print("=" * 40)

    while True:
        print("\nOptions:")
        print("1. Run full scraping pipeline")
        print("2. Search jobs only")
        print("3. View saved jobs")
        print("4. Process unprocessed jobs")
        print("5. Exit")

        choice = input("Choose an option: ").strip()

        if choice == '1':
            jobs = scraper.run_full_pipeline()
            print(f"\nScraped {len(jobs)} jobs successfully!")

        elif choice == '2':
            keywords = input("Enter job keywords (default: AI ML engineer): ").strip() or "AI ML engineer"
            location = input("Enter location (default: India): ").strip() or "India"
            max_jobs = int(input("Max jobs to scrape (default: 20): ").strip() or "20")

            jobs = scraper.search_linkedin_jobs(keywords, location, max_jobs)
            scraper.save_jobs_to_db(jobs)
            print(f"\nFound and saved {len(jobs)} jobs!")

        elif choice == '3':
            jobs = scraper.load_unprocessed_jobs()
            print(f"\nUnprocessed Jobs ({len(jobs)}):")
            for i, job in enumerate(jobs, 1):
                print(f"{i}. {job.title} at {job.company}")
                print(f"   Location: {job.location}")
                print(f"   HR Emails: {', '.join(job.hr_emails) if job.hr_emails else 'None found'}")
                print()

        elif choice == '4':
            jobs = scraper.load_unprocessed_jobs()
            print(f"Processing {len(jobs)} unprocessed jobs...")

            for job in jobs:
                print(f"Processing: {job.title} at {job.company}")
                if not job.description:
                    job.description = scraper.get_job_description(job.job_url)
                if not job.hr_emails:
                    job.hr_emails = scraper.find_company_hr_emails(job.company, job.company_url)

                scraper.save_jobs_to_db([job])
                scraper.mark_job_processed(job.job_url)
                time.sleep(2)

            print("Processing completed!")

        elif choice == '5':
            if scraper.driver:
                scraper.driver.quit()
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
