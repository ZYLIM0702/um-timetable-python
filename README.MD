# UM Timetable Scraper (Python)

A Python-based scraper for Universiti Malaya’s timetable that fetches updated course information frequently. This fork replaces the original Node.js implementation with a faster, asynchronous Python solution using Selenium for cookie retrieval and automated data fetching.

---

## Overview

This project is a fork of the original [UM timetable scraper](https://github.com/damnitjoshua/um-timetable-sdk) and is entirely re-implemented in Python. By leveraging Selenium to automate cookie retrieval and asynchronous programming for concurrent requests, the scraper significantly reduces the overall execution time (approximately *2500* seconds) compared to the original version. The tool fetches both course event and lecturer data from the UM TimeEdit system and outputs raw JSON files for further processing or integration into timetable applications.

---

## Features

- **Python Implementation:** Easier to customize and integrate with other Python projects.
- **Selenium Integration:** Automates browser actions to retrieve authentication cookies seamlessly.
- **Asynchronous Scraping:** Uses concurrent fetching (with configurable concurrency settings) for improved performance.
- **Configurable Parameters:** Quickly adjust concurrency levels, batch delays, page size, and other settings.
- **Automatic JSON Export:** Saves timetable data and lecturer details to JSON files for further processing.

---

## Requirements

- Python 3.7+
- [Selenium](https://pypi.org/project/selenium/)
- [ChromeDriver](https://chromedriver.chromium.org/) (Ensure the version matches your installed Chrome browser)
- Other dependencies listed in `requirements.txt`

---

## Installation

1. **Clone this Repository:**

   ```bash
   git clone https://github.com/your-username/UM-Timetable-Scraper-Py.git
   cd UM-Timetable-Scraper-Py
   ```

2. **Install Python Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up ChromeDriver:**

   - Download ChromeDriver from [here](https://chromedriver.chromium.org/).
   - Ensure it’s accessible via your system’s PATH or specify its location in the code if needed.

---

## Configuration

Before running the scraper, review and update any configurable variables in the code.

- **Concurrency and Timing Settings:**  
  Adjust the following parameters according to your needs:

  ```python
  PAGE_CONCURRENCY = 2         # Number of concurrent page fetches
  RESERVATION_CONCURRENCY = 3  # Number of concurrent reservation detail fetches
  PAGE_SIZE = 100              # Number of items per page request
  BATCH_DELAY = 1.5            # Delay (in seconds) between page batches
  RETRY_BASE_DELAY = 1.0       # Base delay for exponential backoff (in seconds)
  ```

- **Data Range and Output Files:**  
  Define the range of lecturer IDs and the maximum number of items to fetch. Also, set your desired output filenames:

  ```python
  START_LEC_ID = 8600
  END_LEC_ID = 13700
  MAX_ITEMS_TO_FETCH = 35000
  FINAL_FILENAME = "course_events_with_details.json"
  LEC_OUTPUT = "lecturer_details.json"
  ```

---

## Usage

Once you’ve configured the necessary variables, run the scraper with:

```bash
python TimeEdit_Fetch.py
```

The script will:
1. Launch a headless Chrome browser to log in and acquire authentication cookies.
2. Set up necessary HTTP headers.
3. Fetch timetable and lecturer data concurrently.
4. Output raw JSON files with the fetched data.

---

## Contributing

Contributions to enhance performance, add features, or fix issues are very welcome! Please submit issues or pull requests through GitHub. If you have any feature suggestions, let us know in the [issues section](https://github.com/your-username/UM-Timetable-Scraper-Py/issues).

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgements

- Original Node.js version by [damnitjoshua/um-timetable-sdk](https://github.com/damnitjoshua/um-timetable-sdk) – for the inspiration and initial insights into TimeEdit API interactions.
- Selenium and Python community for the libraries and documentation that made this implementation possible.

---
