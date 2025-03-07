from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import subprocess
import threading
import time
import aiohttp
import asyncio
import json
import ssl
import certifi
import re
from bs4 import BeautifulSoup


def create_ssl_context(verify: bool = True):
    """
    Create and return an SSL context.
    If verify is True, use the certifi CA bundle.
    Otherwise, disable SSL certificate verification (insecure).
    """
    if verify:
        return ssl.create_default_context(cafile=certifi.where())
    else:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context



def login_to_timeedit():
    # Open TimeEdit student portal
    driver.get('https://cloud.timeedit.net/my_um/web/students/')

    try:
        login_start_time = time.time()
        while time.time() - login_start_time < 30:
            # Click on the "Log in" button
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "loginAuth"))).click()

            # Click on "Sign in using SSO"
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(), 'Sign in using')]/strong[contains(text(), 'SSO')]"))
            ).click()

            # Login Page
            EMAILFIELD = (By.ID, "i0116")
            PASSWORDFIELD = (By.ID, "i0118")
            NEXTBUTTON = (By.ID, "idSIButton9")

            # Wait for email field and enter email
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(EMAILFIELD)).send_keys("EMAIL@siswa365.um.edu.my")

            # Click Next
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

            # Wait for password field and enter password
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(PASSWORDFIELD)).send_keys("PASSWORD")

            # Click Login
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable(NEXTBUTTON)).click()

            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Yes')]")))
            # Ensure login completes before fetching cookies
            WebDriverWait(driver, 10).until(EC.url_contains("timeedit"))  # Ensure we're on the correct page
            time.sleep(5)  

            # Get cookies
            cookies = driver.get_cookies()
            driver.quit()

            # Extract the required cookie
            for cookie in cookies:
                if cookie['name'] == 'TEmy_umweb':
                    return cookie['value']

                print("Cookie 'TEmy_umweb' not found!")
                return None
        
        print("Login timeout reached!")
        driver.quit()
        return None
    
    except Exception as e:
        cookies = driver.get_cookies()
        driver.quit()

        # Extract the required cookie
        for cookie in cookies:
            if cookie['name'] == 'TEmy_umweb':
                return cookie['value']
            
        print(f"Final Error: {e}")
        driver.quit()
        return None
    
async def fetch_lecturer_info(lecturer_id):
    base_url = "https://cloud.timeedit.net/my_um/web/students/"
    url = f"{base_url}objects/{lecturer_id}/o.json?fr=t&types=15&sid=5&l=en_US"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=HEADERS, ssl=ssl_context) as response:
                if response.status != 200:
                    return None
                return await response.json()
    except Exception as e:
        print(f"Error fetching lecturer {lecturer_id}: {e}")
        return None

async def process_lecturer_batch(batch_ids):
    async def fetch_data(lecturer_id):
        data = await fetch_lecturer_info(lecturer_id)
        return {'id': lecturer_id, 'details': data} if data and "Job Category" in data else None

    tasks = [fetch_data(lecturer_id) for lecturer_id in batch_ids]
    results = await asyncio.gather(*tasks)
    return [result for result in results if result]

async def process_lecturers_concurrently():
    start_lecturer_id = START_LEC_ID
    end_lecturer_id = END_LEC_ID
    batch_size = 100
    concurrency_limit = 10
    all_lecturer_data = []
    all_batches = []

    print(f"Fetching lecturer data for IDs {start_lecturer_id} to {end_lecturer_id}")

    # Generate all batches first
    for i in range(start_lecturer_id, end_lecturer_id + 1, batch_size):
        all_batches.append(list(range(i, min(i + batch_size, end_lecturer_id + 1))))

    # Process batches in concurrent groups
    for i in range(0, len(all_batches), concurrency_limit):
        batch_group = all_batches[i:i + concurrency_limit]
        print(f"Processing group {i + 1}-{i + len(batch_group)} of {len(all_batches)}")
        group_results = await asyncio.gather(
            *[process_lecturer_batch(batch) for batch in batch_group]
        )
        print("Total lecturers: ", len(all_lecturer_data))

        
        all_lecturer_data.extend([item for sublist in group_results for item in sublist])

    print("Fetching complete. Total lecturers:", len(all_lecturer_data))

    if all_lecturer_data:
        with open(LEC_OUTPUT, 'w') as f:
            json.dump(all_lecturer_data, f, indent=2)
        print("JSON file downloaded")


async def fetch_with_retry(session, url, method="GET", headers=None, ssl_context=None,
                           parse_json=False, content_type=None, description=""):
    attempt = 0
    while True:
        attempt += 1
        try:
            async with session.request(method, url, headers=headers, ssl=ssl_context) as response:
                if response.status == 200:
                    if parse_json:
                        return await response.json(content_type=content_type)
                    else:
                        return await response.text()
                else:
                    print(f"[DEBUG] {description}: URL {url} returned status {response.status} (attempt {attempt})")
        except Exception as e:
            print(f"[DEBUG] {description}: Exception fetching URL {url} on attempt {attempt}: {e}")
        delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
        await asyncio.sleep(min(delay, 10))


async def get_object_details(session, base_url, object_id):
    url = f"{base_url}objects/{object_id}/o.json?fr=t&types=15&sid=5&l=en_US"
    description = f"get_object_details for object {object_id}"
    return await fetch_with_retry(session, url, headers=HEADERS, ssl_context=ssl_context,
                                  parse_json=True, description=description)

async def get_course_events(session, base_url, course_id):
    url = f"{base_url}ri.json?h=f&sid=3&p=0.m,12.n&objects={course_id}&ox=0&types=0&fe=0&h2=f&l=en_EN"
    description = f"get_course_events for course {course_id}"
    data = await fetch_with_retry(session, url, headers=HEADERS, ssl_context=ssl_context,
                                  parse_json=True, description=description)
    if data and 'reservations' in data and 'columnheaders' in data:
        reservations = [{
            **rese,
            'additional_info': { key: rese['columns'][index] for index, key in enumerate(data['columnheaders']) }
        } for rese in data['reservations']]
        data['reservations'] = reservations
        return data
    else:
        print(f"[DEBUG] get_course_events: Invalid data format for course {course_id}")
        return None

async def get_reservation_details_html(session, base_url, reservation_id):
    url = f"{base_url}ri.html?h=f&sid=3&types=4&fe=0&h2=f&l=en_EN&id={reservation_id}&fr=t&step=0&ef=2&nocache=2"
    description = f"get_reservation_details_html for reservation {reservation_id}"
    return await fetch_with_retry(session, url, headers=HEADERS, ssl_context=ssl_context,
                                  parse_json=False, description=description)

async def parse_reservation_details_from_html(html):
    if not html:
        return None
    soup = BeautifulSoup(html, 'html.parser')
    details = {}
    detail_table = soup.select_one('.detailedResObjects')
    if detail_table:
        rows = detail_table.find_all('tr')
        for row in rows:
            column_name_cell = row.select_one('.columnname')
            value_cell = row.select_one('.pr')
            if column_name_cell and value_cell:
                column_name = column_name_cell.get_text(strip=True)
                value = value_cell.get_text(strip=True)
                details[column_name] = value
    return details

async def get_total_objects(session, base_url):
    """
    Fetch an initial page to determine the total number of objects.
    Looks for a text like 'Search result: 1234' in the HTML.
    """
    url = f"{base_url}objects.html?max=1&fr=t&partajax=t&im=f&sid=4&l=en_US&types=15"
    description = "get_total_objects"
    html = await fetch_with_retry(session, url, headers=HEADERS, ssl_context=ssl_context,
                                  parse_json=False, description=description)
    match = re.search(r"Search result:?\s*(\d+)", html, re.IGNORECASE)
    if match:
        total = int(match.group(1))
        print(f"[DEBUG] Total objects found: {total}")
        return total
    else:
        print("[DEBUG] Total objects count not found, using default max_items")
        return None

async def process_object(session, base_url, item_div):
    """
    Process a single object element: fetch its details and events,
    then for each event, load reservation details.
    """
    object_id = item_div.get('data-idonly')
    if not object_id:
        return None
    try:
        details_task = asyncio.create_task(get_object_details(session, base_url, object_id))
        events_task = asyncio.create_task(get_course_events(session, base_url, object_id))
        details, events_data = await asyncio.gather(details_task, events_task)
        events = events_data['reservations'] if events_data and 'reservations' in events_data else []
        if events:
            sem = asyncio.Semaphore(RESERVATION_CONCURRENCY)
            async def process_reservation(reservation):
                async with sem:
                    html = await get_reservation_details_html(session, base_url, reservation['id'])
                    reservation['html_details'] = await parse_reservation_details_from_html(html)
            await asyncio.gather(*(process_reservation(r) for r in events))
        return {
            'id': item_div.get('data-id'),
            'idOnly': object_id,
            'type': item_div.get('data-type'),
            'name': item_div.get('data-name'),
            'details': details,
            'events': events
        }
    except Exception as e:
        print(f"[DEBUG] process_object: Exception processing object {object_id}: {e}")
        return None

async def process_page(session, base_url, page_url):
    """
    Process one page: fetch HTML, parse object items and process each.
    """
    try:
        html = await fetch_with_retry(session, page_url, headers=HEADERS, ssl_context=ssl_context,
                                      parse_json=False, description=f"process_page: {page_url}")
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.select('[data-idonly]')
        objects = await asyncio.gather(*(process_object(session, base_url, item) for item in items))
        valid_objects = [obj for obj in objects if obj is not None]
        return valid_objects
    except Exception as e:
        print(f"[DEBUG] process_page: Exception processing page {page_url}: {e}")
        return []

async def get_all_objects(session, base_url, max_items=35000):
    """
    Determine total objects to load (using an initial request) then generate page URLs
    and process each page concurrently with a controlled number of simultaneous fetches.
    """
    all_objects = []
    total_objects = await get_total_objects(session, base_url)
    if total_objects is None:
        total_objects = max_items
    else:
        total_objects = min(total_objects, max_items)
    page_urls = []
    for start in range(0, total_objects, PAGE_SIZE):
        page_url = f"{base_url}objects.html?max={PAGE_SIZE}&fr=t&partajax=t&im=f&sid=4&l=en_US&types=15&start={start}"
        page_urls.append(page_url)
    sem = asyncio.Semaphore(PAGE_CONCURRENCY)
    async def sem_page(url):
        async with sem:
            objects = await process_page(session, base_url, url)
            # Delay between batches to avoid overwhelming the server.
            await asyncio.sleep(BATCH_DELAY)
            print(f"Processed a page; cumulative objects so far: {len(all_objects) + len(objects)}")
            return objects
    pages_results = await asyncio.gather(*(sem_page(url) for url in page_urls))
    for page_objs in pages_results:
        all_objects.extend(page_objs)
    return all_objects[:max_items]



# Set up the WebDriver
options = webdriver.ChromeOptions()
options.set_capability("goog:loggingPrefs", {"performance": "ALL"}) 
options.add_argument("--auto-open-devtools-for-tabs")
options.add_argument("--disable-cache")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)
driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
ssl_context = create_ssl_context(verify=True)
# ---------------- Configurable parameters ----------------
PAGE_CONCURRENCY = 2         # concurrent page fetches
RESERVATION_CONCURRENCY = 3  # concurrent reservation detail fetches
PAGE_SIZE = 100              # items per page request
BATCH_DELAY = 1.5            # delay (in seconds) between page batches
RETRY_BASE_DELAY = 1.0       # base delay for exponential backoff (in seconds)
# ----------------------------------------------------------
# Updated headers with referer and x-requested-with added.
START_LEC_ID=8600
END_LEC_ID=13700
MAX_ITEMS_TO_FETCH=35000
FINAL_FILENAME="course_events_with_details.json"
LEC_OUTPUT="lecturer_details.json"
async def main():
    total_start_time = time.time()
    global COOKIES
    COOKIES = None
    while COOKIES is None:
        COOKIES = login_to_timeedit()
    print(COOKIES)
    global HEADERS
    HEADERS = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "cookie": f"TEmy_umweb={COOKIES}",
        "dnt": "1",
        "pragma": "no-cache",
        "referer": "https://cloud.timeedit.net/my_um/web/students/",
        "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    base_url = "https://cloud.timeedit.net/my_um/web/students/"
    if not base_url.endswith("/"):
        base_url += "/"
    max_items_to_fetch = MAX_ITEMS_TO_FETCH
    await process_lecturers_concurrently()
    async with aiohttp.ClientSession() as session:
        objects_with_events = await get_all_objects(session, base_url, max_items_to_fetch)
        final_filename = FINAL_FILENAME
        try:
            with open(final_filename, 'w') as f:
                json.dump(objects_with_events, f, indent=2)
            print(f"[DEBUG] Final data written to {final_filename}")
        except Exception as e:
            print(f"[DEBUG] Exception writing final file: {e}")
    
    params = ["course_events_with_details.json", "lecturer_data.json"]

    # Clean the data using the Node.js script
    result = subprocess.run(["node", "cleaner.js"] + params, capture_output=True, text=True)
    print(result.stdout)
    total_end_time = time.time()
    print(f"Total time taken: {total_end_time - total_start_time:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
