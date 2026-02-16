import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from chromedriver_py import binary_path
import time
import re
import tempfile
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
from urllib.parse import quote

def get_extension_id_from_url(url: str) -> str | None:
    try:
        parts = [p for p in urlparse(url).path.split("/") if p]
        # expected: ["detail", "<name>", "<id>"]
        if len(parts) >= 3 and parts[0] == "detail":
            ext_id = parts[-1]
            if re.fullmatch(r"[a-p]{32}", ext_id): 
                return ext_id
    except Exception:
        pass
    return None

def make_crx_download_url(ext_id: str, prodversion: str = "120.0.0.0") -> str:
    x = f"id%3D{ext_id}%26uc"
    return (
        "https://clients2.google.com/service/update2/crx"
        f"?response=redirect&prodversion={quote(prodversion)}"
        "&acceptformat=crx2,crx3"
        f"&x={x}"
    )

# Set up the Chrome WebDriver using chromedriver_py
service = Service(binary_path)
temp_dir = tempfile.mkdtemp()
options = Options()

options.add_argument(f"--user-data-dir={temp_dir}")
options.add_argument("--no-sandbox")  
options.add_argument("--disable-dev-shm-usage")
options.add_argument( "--remote-debugging-pipe" )
svc = webdriver.ChromeService(executable_path=binary_path)
driver = webdriver.Chrome(service=svc, options=options)


# Visit the Chrome Web Store URL
# url = "https://chromewebstore.google.com/category/extensions/productivity/tools"
url = "https://chromewebstore.google.com/category/extensions/productivity/communication?hl=en&authuser=1&sortBy=highestRated&filterBy=featured"
driver.get(url)

time.sleep(5)

# Ask user for the number of times to click "Load More"
num_load_more_clicks = int(input("Enter the number of times to click the 'Load More' button: "))

# Click the 'Load More' button the specified number of times
for _ in range(num_load_more_clicks):
    try:
        # load_more_button = driver.find_element(By.XPATH, '//span[@class="mUIrbf-vQzf8d"]')
        load_more_button = driver.find_element(
            By.XPATH,
            '//button[.//span[normalize-space()="Load more"]]'
        )

        ActionChains(driver).move_to_element(load_more_button).click(load_more_button).perform()
        print("Clicked 'Load More' button.")
        time.sleep(5)  # Wait for more cards to load
    except Exception:
        print("No 'Load More' button found or unable to click.")
        break  # Exit the loop if no more cards can be loaded

# Ask user for the starting and ending range
start_range = int(input("Enter the starting card number (e.g., 1): "))
end_range = int(input("Enter the ending card number (e.g., 80): "))

# Calculate the total number of cards to fetch
total_cards_to_fetch = end_range - start_range + 1
if total_cards_to_fetch <= 0:
    print("Invalid range. Ending range must be greater than or equal to the starting range.")
    driver.quit()
    exit()

# Initialize a list to store the data for each card
data = []

# Track the number of cards processed
cards_processed = 0
current_card_index = 0  # To keep track of the card index across multiple loads

try:
    while cards_processed < total_cards_to_fetch:
        # Find all the card containers using class name and jsname
        cards = driver.find_elements(By.XPATH, '//*[@class="cD9yc" and @jsname="hs2VQd"]')

        for i in range(len(cards)):
            current_card_index += 1

            # Skip cards that are before the starting range
            if current_card_index < start_range:
                continue

            # Stop processing if we have reached the desired number of cards
            if cards_processed >= total_cards_to_fetch:
                break

            # Get the card container at index `i`
            card = cards[i]

            # For each card, find the title inside <p> tag
            card_title = card.find_element(By.XPATH, './/p[@class="GzKZcb"]')

            # Find the <a> tag and get the href attribute
            card_link = card.find_element(By.XPATH, './/a[@class="UvhDdd" and @jsname="qcuvSe"]')
            card_href = card_link.get_attribute('href')

            # Print the title and href of each card
            print(f"Card {current_card_index} Title:", card_title.text)
            print(f"Card {current_card_index} Href:", card_href)

            # Initialize dictionary to store data for the current card
            card_data = {
                "Card Title": card_title.text,
                "Card Href": card_href
            }
            
            ext_id = get_extension_id_from_url(card_href)
            card_data["Extension ID"] = ext_id if ext_id else "N/A"

            # Open the card's href in a new tab
            driver.execute_script(f"window.open('{card_href}', '_blank');")
            time.sleep(2)

            # Switch to the new tab
            driver.switch_to.window(driver.window_handles[1])

            # Wait for the page to load
            time.sleep(5)

            # Extract the title (h1 tag)
            try:
                page_title = driver.find_element(By.XPATH, '//h1[@class="Pa2dE"]')
                card_data["Page Title"] = page_title.text
                print("Page Title:", page_title.text)
            except Exception:
                card_data["Page Title"] = "N/A"
                print("Page Title: N/A")

            # Extract the updated date and version number
            try:
                updated_date = driver.find_element(By.XPATH, '//ul[@class="TKAMQe"]//li[div[text()="Updated"]]/div[2]')
                card_data["Updated Date"] = updated_date.text
                print("Updated Date:", updated_date.text)
            except Exception:
                card_data["Updated Date"] = "N/A"
                print("Updated Date: N/A")

            try:
                version = driver.find_element(By.XPATH, '//ul[@class="TKAMQe"]//li[div[text()="Version"]]/div[2]')
                card_data["Version"] = version.text
                print("Version:", version.text)
            except Exception:
                card_data["Version"] = "N/A"
                print("Version: N/A")

            # Extract "Offered By"
            offered_by = "N/A"
            try:
                offered_by = driver.find_element(By.XPATH, '//li[@class="ZbWJPd T7iRm"]//div[2]').text.strip()
                print("Offered By :", offered_by)
            except Exception:
                try:
                    offered_by = driver.find_element(By.XPATH, '//div[@class="odyJv"]//a').get_attribute('href')
                    print("Offered By :", offered_by)
                except Exception:
                    try:
                        offered_by = driver.find_element(By.XPATH, '//a[@class="cJI8ee"]').text.strip()
                        print("Offered By :", offered_by)
                    except Exception:
                        pass
            card_data["Offered By"] = offered_by

            # Extract the number of users
            try:
                num_users = driver.find_element(By.XPATH, '//div[@class="F9iKBc"]').text.strip()
                users_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s+users', num_users)
                card_data["Number of Users"] = users_match.group(1) if users_match else "N/A"
                print("Number of Users:", card_data["Number of Users"])
            except Exception:
                card_data["Number of Users"] = "N/A"
                print("Number of Users: N/A")

            # Extract the rating
            try:
                rating = driver.find_element(By.XPATH, '//span[@class="Vq0ZA"]')
                card_data["Rating"] = rating.text
                print("Rating:", rating.text)
            except Exception:
                card_data["Rating"] = "N/A"
                print("Rating: N/A")

            # Extract total number of ratings
            try:
                total_ratings = driver.find_element(By.XPATH, '//p[@class="xJEoWe"]')
                card_data["Total Ratings"] = total_ratings.text
                print("Total Ratings:", total_ratings.text)
            except Exception:
                card_data["Total Ratings"] = "N/A"
                print("Total Ratings: N/A")

            # Add the data to the list
            data.append(card_data)

            # Increment the count of processed cards
            cards_processed += 1

            # Print a separator line for clarity
            print("-----------")

            # Close the new tab
            driver.close()

            # Switch back to the main page tab
            driver.switch_to.window(driver.window_handles[0])

            # Wait for the main page to load
            time.sleep(5)

            # Re-locate the card containers after returning to the main page
            cards = driver.find_elements(By.XPATH, '//*[@class="cD9yc" and @jsname="hs2VQd"]')

except Exception as e:
    print("Error:", e)

# Close the browser after scraping
driver.quit()

# Create a pandas DataFrame from the list of dictionaries
df = pd.DataFrame(data)

# Write the DataFrame to a CSV file
df.to_csv('chrome_web_store_scraped_data.csv', index=False)

print("Data has been written to 'chrome_web_store_scraped_data.csv'")
