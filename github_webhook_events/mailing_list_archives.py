import aiohttp
import asyncio
from aiohttp import ClientSession
from typing import AsyncGenerator, List
from bs4 import BeautifulSoup
from email.message import EmailMessage

class W3CEmailClient:
    def __init__(self, session: ClientSession, group_slug: str):
        self.session = session
        self.group_slug = group_slug
        self.base_url = "https://www.w3.org/Search/Mail/Public/advanced_search"
        self.results_per_page = 20

    async def _fetch_page(self, month: str, year: int, page: int) -> List[EmailMessage]:
        params = {
            "period_month": month,
            "period_year": str(year),
            "index-grp": "Public__FULL",
            "index-type": "t",
            "type-index": self.group_slug,
            "resultsperpage": self.results_per_page,
            "sortby": "date",
            "page": str(page)
        }
        async with self.session.get(self.base_url, params=params) as response:
            response.raise_for_status()
            data = await response.text()
            return self._extract_emails(data)

    def _extract_emails(self, html: str) -> List[EmailMessage]:
        soup = BeautifulSoup(html, 'html.parser')
        emails = []

        # Locate email messages in the HTML and extract relevant details
        messages = soup.find_all('main', class_='mail')

        for message in messages:
            email_msg = EmailMessage()

            # Extracting the header information
            from_tag = message.find('span', class_='from')
            if from_tag:
                email_msg['From'] = from_tag.text.replace('From: ', '').strip()

            date_tag = message.find('span', class_='date')
            if date_tag:
                email_msg['Date'] = date_tag.text.replace('Date: ', '').strip()

            subject_tag = message.find('title')
            if subject_tag:
                email_msg['Subject'] = subject_tag.text.strip()

            to_tag = message.find('span', class_='to')
            if to_tag:
                email_msg['To'] = to_tag.text.replace('To: ', '').strip()

            # Extracting the body of the message
            body = message.find('pre', class_='body')
            if body:
                email_msg.set_content(body.text.strip())

            emails.append(email_msg)

        return emails

    async def fetch_emails(self, start_year: int, end_year: int) -> AsyncGenerator[EmailMessage, None]:
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        tasks = []
        for year in range(start_year, end_year + 1):
            for month in months:
                tasks.append(self._fetch_page(month, year, 1))  # Start with the first page

        # Gather initial page results concurrently
        initial_pages = await asyncio.gather(*tasks)

        for page_emails in initial_pages:
            for email in page_emails:
                yield email

        # Now handle pagination: check if there are more pages and fetch them
        for year in range(start_year, end_year + 1):
            for month in months:
                page = 2  # Start from the second page
                while True:
                    try:
                        emails = await self._fetch_page(month, year, page)
                        if not emails:
                            break
                        for email in emails:
                            yield email
                        page += 1
                    except aiohttp.ClientResponseError:
                        break

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.session.close()

# Usage example
async def main():
    async with aiohttp.ClientSession() as session:
        client = W3CEmailClient(session, "public-webauthn")
        async for email in client.fetch_emails(2023, 2024):
            print(email)

if __name__ == "__main__":
    asyncio.run(main())
