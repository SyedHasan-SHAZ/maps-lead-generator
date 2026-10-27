import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def scrape_google_maps(query: str):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

    # Cloud Docker container vs Local machine check
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
        service = Service(executable_path=os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    leads = []
    try:
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        try:
            feed = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
        except Exception:
            return leads

        last_height = driver.execute_script("return arguments[0].scrollHeight", feed)
        for _ in range(8):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            time.sleep(2.5)
            new_height = driver.execute_script("return arguments[0].scrollHeight", feed)
            if new_height == last_height:
                break
            last_height = new_height

        results = driver.find_elements(By.CLASS_NAME, 'hfpxzc')

        for r in results[:25]:
            try:
                driver.execute_script("arguments[0].click();", r)
                time.sleep(2)

                try:
                    name = driver.find_element(By.CSS_SELECTOR, 'h1.DUwDvf').text.strip()
                except Exception:
                    continue

                if not name:
                    continue

                phone = None
                try:
                    phone_elem = driver.find_element(By.XPATH, '//button[contains(@data-item-id, "phone:tel:")]')
                    phone = phone_elem.text.strip()
                except Exception:
                    pass

                website = None
                try:
                    web_elem = driver.find_element(By.XPATH, '//a[contains(@data-item-id, "authority")]')
                    website = web_elem.get_attribute('href')
                except Exception:
                    pass

                address = query
                try:
                    addr_elem = driver.find_element(By.XPATH, '//button[contains(@data-item-id, "address")]')
                    address = addr_elem.text.strip()
                except Exception:
                    pass

                if not website and phone:
                    clean_phone = "".join(filter(str.isdigit, phone))
                    leads.append({
                        "business_name": name,
                        "phone_number": phone,
                        "whatsapp_phone": clean_phone,
                        "address": address
                    })
            except Exception:
                continue

    finally:
        driver.quit()

    return leads