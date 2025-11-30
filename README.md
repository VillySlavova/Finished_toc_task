# Domain Manager

Domain Manager is a simple Django application that manages domains and runs automated collectors in the background.  
It was created as part of a technical task and demonstrates:

- Adding and validating domains (FQDN)
- Running collectors in background threads (Scraper & WHOIS)
- Preventing the UI from freezing while collectors run
- Automatically saving emails/phones found by collectors
- Displaying all collected contacts
- Managing collectors (start, stop, enable, disable)

---

## Features

### Add Site
- Enter a domain (FQDN)
- Domain is validated
- If the domain is new, two collectors start automatically:
  - **Scraper** – crawls pages and extracts emails/phones
  - **WHOIS** – reads WHOIS data for contact info

### All Contacts
- Shows all collected contact information
- Displays which collector found each contact

### Collectors
- Shows every collector (past and present)
- Status: pending / running / finished / failed / stopped
- Actions: **Start**, **Stop**, **Enable**, **Disable**
- If a collector type is disabled, it will NOT run for new domains

---

## Technical Overview
- Python + Django
- Django JET (community version)
- Background workers using Python threads
- `requests` + `BeautifulSoup` for scraping
- `python-whois` for WHOIS lookups
- SQLite for development database

---

## How to Run
1) git clone https://github.com/VillySlavova/Finished_toc_task.git

2) cd Finished_toc_task

3) python -m venv venv

4) venv\Scripts\activate

5) pip install -r requirements.txt

6) python manage.py migrate

7) python manage.py createsuperuser

8) python manage.py runserver
