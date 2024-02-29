from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
from bs4 import BeautifulSoup
import time
import pandas as pd

# Configure Selenium WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)

browser = webdriver.Chrome(options=chrome_options)

# Open the initial page
url = "https://www.payscale.com/college-salary-report/majors-that-pay-you-back/bachelors"
browser.get(url)

data = []
headers_added = False  # Flag to track if headers have been added to the dataset

try:
    while True:
        # Parse the current page's content using BeautifulSoup
        soup = BeautifulSoup(browser.page_source, "html.parser")
        table = soup.find("table", {"class": "data-table"})
        rows = table.find_all("tr")

        for row in rows:
            # Check if the row is a header by looking for 'th' elements
            if row.find("th"):
                if not headers_added:
                    headers = [header.text.strip() for header in row.find_all("th")]
                    data.append(headers)
                    headers_added = True
                continue  # Skip the header row if headers have already been added

            cols = row.find_all(["td", "th"])
            row_data = [ele.text.strip() for ele in cols]
            data.append(row_data)

        # Scroll to the pagination section
        try:
            # Wait for the next button to be clickable and visible
            next_button = WebDriverWait(browser, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".pagination__next-btn"))
            )

            # Scroll the page to bring the next button into view
            browser.execute_script("arguments[0].scrollIntoView(true);", next_button)
            time.sleep(1)  # Brief pause to ensure page has adjusted to the scroll

            if "pagination__btn--off" in next_button.get_attribute("class"):
                print("Last page reached.")
                break
            else:
                next_button.click()
                time.sleep(3)  # Wait for the next page to load completely
        except TimeoutException:
            print("Failed to find the next button or page took too long to respond.")
            break

except NoSuchElementException:
    print("An element was not found. This might be due to a change in the website's structure.")
except WebDriverException:
    print("Webdriver encountered an issue.")
finally:
    # Write data to CSV after scraping
    with open("raw_major_salary.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(data)
    # Close the browser
    browser.quit()


df = pd.read_csv("output.csv")

for column in df.columns:
    df[column] = df[column].str.split(":").str[1]

# Now, strip the dollar sign and commas from the salary columns and convert to float
df["Early Career Pay"] = df["Early Career Pay"].str.replace("[$,]", "", regex=True).astype(float)
df["Mid-Career Pay"] = df["Mid-Career Pay"].str.replace("[$,]", "", regex=True).astype(float)

# Convert the High Meaning percentage to a float, handling non-convertible strings
df["% High Meaning"] = pd.to_numeric(df["% High Meaning"].str.rstrip("%"), errors="coerce") / 100

# Finally, strip any leading space that may be left after splitting
df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)

# Write the cleaned DataFrame to a new CSV file
df.to_csv("clean_major_salary.csv", index=False, encoding="utf-8")
