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
    options.add_argument("--lang=en-US")
    
    # --- STEALTH OPTIONS (Google Maps bot detection bypass) ---
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    # Cloud Docker container vs Local machine check
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
        service = Service(executable_path=os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver"))
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Hide webdriver property from JavaScript detection
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    leads = []
    try:
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}?hl=en"
        driver.get(url)
        
        wait = WebDriverWait(driver, 15)
        
        # Handle Google consent popup if it appears
        try:
            accept_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[contains(., "Accept all") or contains(., "I agree")]')))
            accept_btn.click()
            time.sleep(2)
        except Exception:
            pass

        try:
            feed = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]')))
        except Exception as e:
            print(f"Feed element not found: {e}")
            return leads

        last_height = driver.execute_script("return arguments[0].scrollHeight", feed)
        for _ in range(6):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            time.sleep(2)
            new_height = driver.execute_script("return arguments[0].scrollHeight", feed)
            if new_height == last_height:
                break
            last_height = new_height

        # Robust selector for listings
        results = driver.find_elements(By.CSS_SELECTOR, 'a.hfpxzc, a[href*="/maps/place/"]')
        print(f"Found {len(results)} raw business links on Maps.")

        seen_links = set()
        unique_results = []
        for r in results:
            try:
                href = r.get_attribute('href')
                if href and href not in seen_links and '/maps/place/' in href:
                    seen_links.add(href)
                    unique_results.append(r)
            except:
                continue

        for r in unique_results[:20]:
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

    except Exception as ex:
        print(f"Scraper general error: {ex}")
    finally:
        driver.quit()

    return leads
