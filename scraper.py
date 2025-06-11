import csv, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_prices(input_path, output_path, log_path, job_id):
    # Replace these with your real login credentials
    USERNAME = "potravinysventek@gmail.com"
    PASSWORD = "71020799As"

    # Set up headless Chrome
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    wait = WebDriverWait(driver, 10)

    # Load barcodes from CSV
    with open(input_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        barcodes = [row["Barcode"].strip() for row in reader if row["Barcode"].strip()]

    results = []

    with open(log_path, "w", encoding="utf-8") as log:
        log.write(f"🔐 Logging in to vokollar.sk...\n")
        try:
            driver.get("https://obchod.vokollar.sk/")

            # Click login trigger to show modal
            login_trigger = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'a.ct-account-item[href="#account-modal"]')
            ))
            login_trigger.click()

            # Wait for modal and login fields
            wait.until(EC.visibility_of_element_located((By.ID, "account-modal")))
            user_input = wait.until(EC.presence_of_element_located((By.ID, "user_login")))
            pass_input = driver.find_element(By.ID, "user_pass")
            submit_btn = driver.find_element(By.NAME, "wp-submit")

            user_input.send_keys(USERNAME)
            pass_input.send_keys(PASSWORD)
            submit_btn.click()
            time.sleep(3)

            log.write("✅ Logged in successfully\n\n")
        except Exception as e:
            log.write(f"❌ Login failed: {e}\n")
            driver.quit()
            return

        log.write(f"🔍 Loaded {len(barcodes)} barcodes\n")

        for barcode in barcodes:
            log.write(f"Looking up {barcode}...\n")
            try:
                driver.get("https://obchod.vokollar.sk/")
                time.sleep(2)

                search_input = driver.find_element(By.ID, "dgwt-wcas-search-input-3")
                search_input.clear()
                search_input.send_keys(barcode)
                search_input.send_keys(Keys.RETURN)
                time.sleep(3)

                try:
                    suggestion = driver.find_element(By.CSS_SELECTOR, ".dgwt-wcas-suggestion")
                    suggestion.click()
                    time.sleep(2)
                except NoSuchElementException:
                    pass

                try:
                    product_name = driver.find_element(By.CSS_SELECTOR, "h1.product_title").text
                except NoSuchElementException:
                    product_name = "Not found"

                try:
                    price_element = driver.find_element(By.CSS_SELECTOR, "p.price span.woocommerce-Price-amount bdi")
                    price = price_element.text.strip()
                except NoSuchElementException:
                    price = "Not found"

                results.append({"Barcode": barcode, "Product": product_name, "Price": price})
                log.write(f"→ {product_name} = {price}\n")

            except Exception as e:
                log.write(f"[!] Error for {barcode}: {str(e)}\n")
                results.append({"Barcode": barcode, "Product": "Error", "Price": "Error"})

            log.flush()

        log.write("\n✅ Scraping complete!\n")

    driver.quit()

    with open(output_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Barcode", "Product", "Price"])
        writer.writeheader()
        writer.writerows(results)
