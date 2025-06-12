import csv, time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_prices(input_path, output_path, log_path, job_id):
    # Replace with real credentials or use environment variables later
    USERNAME = "potravinysventek@gmail.com"
    PASSWORD = "71020799As"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    with open(input_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        barcodes = [row["Barcode"].strip() for row in reader if row["Barcode"].strip()]

    results = []

    with open(log_path, "w", encoding="utf-8") as log:
        try:
            log.write("🔐 Starting login sequence...\n")
            driver.get("https://obchod.vokollar.sk/")

            # Use JS to click login trigger in case of animation issues
            driver.execute_script("document.querySelector('a.ct-account-item').click();")
            time.sleep(2)  # Give modal time to fully render

            # Wait for login modal and input fields
            user_input = wait.until(EC.presence_of_element_located((By.ID, "user_login")))
            pass_input = driver.find_element(By.ID, "user_pass")
            submit_btn = driver.find_element(By.NAME, "wp-submit")

            user_input.send_keys(USERNAME)
            pass_input.send_keys(PASSWORD)
            submit_btn.click()
            time.sleep(3)  # Allow login to complete

            log.write("✅ Logged in successfully\n\n")

        except Exception as e:
            log.write(f"❌ Login failed: {e}\n")
            # Dump HTML for debugging
            with open("/tmp/render_debug.html", "w", encoding="utf-8") as html_debug:
                html_debug.write(driver.page_source)
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
