import csv, time, base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def scrape_prices(input_path, output_path, log_path, job_id):
    USERNAME = "potravinysventek@gmail.com"
    PASSWORD = "71020799As"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    actions = ActionChains(driver)

    with open(input_path, newline='', encoding="utf-8") as f:
        reader = csv.DictReader(f)
        barcodes = [row["Barcode"].strip() for row in reader if row["Barcode"].strip()]

    results = []

    with open(log_path, "w", encoding="utf-8") as log:
        try:
            log.write("🔐 Logging into vokollar.sk...\n")
            driver.get("https://obchod.vokollar.sk/")
            driver.execute_script("document.querySelector('a.ct-account-item').click();")
            time.sleep(1)

            wait.until(EC.visibility_of_element_located((By.ID, "account-modal")))
            user_input = wait.until(EC.presence_of_element_located((By.ID, "user_login")))
            user_input.clear()
            user_input.send_keys(USERNAME)

            pass_input = wait.until(EC.presence_of_element_located((By.ID, "user_pass")))
            pass_input.clear()
            pass_input.send_keys(PASSWORD)

            submit_btn = wait.until(EC.element_to_be_clickable((By.NAME, "wp-submit")))
            submit_btn.click()
            time.sleep(3)

            log.write("✅ Logged in successfully\n\n")

        except Exception as e:
            log.write(f"❌ Login failed: {e}\n")
            with open("/tmp/render_debug_login.html", "w", encoding="utf-8") as html_debug:
                html_debug.write(driver.page_source)
            log.write("📄 Wrote login debug HTML to /tmp/render_debug_login.html\n")
            driver.quit()
            return

        log.write(f"🔍 Loaded {len(barcodes)} barcodes\n")

        for barcode in barcodes:
            log.write(f"🔎 Looking up {barcode}...\n")
            try:
                driver.get("https://obchod.vokollar.sk/")
                time.sleep(2)

                search_input = wait.until(EC.element_to_be_clickable((By.ID, "dgwt-wcas-search-input-3")))
                driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
                actions.move_to_element(search_input).click().perform()
                time.sleep(0.5)

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
                except Exception as e:
                    product_name = "Not found"
                    log.write(f"[!] Product name error for {barcode}: {e}\n")

                try:
                    price_element = driver.find_element(By.CSS_SELECTOR, "p.price span.woocommerce-Price-amount bdi")
                    price = price_element.text.strip()
                except Exception as e:
                    price = "Not found"
                    log.write(f"[!] Price error for {barcode}: {e}\n")

                results.append({"Barcode": barcode, "Product": product_name, "Price": price})
                log.write(f"→ {product_name} = {price}\n")

            except Exception as e:
                log.write(f"[!] Unexpected error for {barcode}: {str(e)}\n")
                results.append({"Barcode": barcode, "Product": "Error", "Price": "Error"})

            log.flush()

        log.write("\n✅ Scraping complete!\n")

        # Embed final HTML for debugging directly in log
        try:
            html = driver.page_source
            encoded = base64.b64encode(html.encode("utf-8")).decode("utf-8")
            log.write("\n[DEBUG_HTML_START]\n")
            log.write(encoded)
            log.write("\n[DEBUG_HTML_END]\n")
            log.write("📄 Embedded debug HTML as base64 between DEBUG_HTML_START and DEBUG_HTML_END\n")
        except Exception as e:
            log.write(f"⚠️ Could not base64-encode HTML: {e}\n")

    driver.quit()

    with open(output_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Barcode", "Product", "Price"])
        writer.writeheader()
        writer.writerows(results)
