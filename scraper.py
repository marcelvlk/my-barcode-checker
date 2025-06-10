import csv, time
from selenium import webdriver
from selenium.webdriver.common.by import By

def scrape_prices(input_path, output_path, log_path, job_id):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    with open(input_path, newline='') as f:
        barcodes = [row[0].strip() for row in csv.reader(f)]

    results = []
    with open(log_path, "w", encoding="utf-8") as log:
        for code in barcodes:
            log.write(f"Searching for barcode: {code}\n")
            try:
                url = f"https://www.libex.sk/default.aspx?content=SHOP&nparams=typ_t;;search;{code};rozsah;G;kde;ALL;ako;ALL"
                driver.get(url)
                time.sleep(2)
                name = driver.find_element(By.CSS_SELECTOR, "#pageForm b").text
                price = driver.find_element(By.CSS_SELECTOR, "#pageForm").text.split("\n")[1]
                results.append([code, name, price])
                log.write(f"✔ {code}: {name} - {price}\n")
            except Exception as e:
                results.append([code, "NOT FOUND", ""])
                log.write(f"✘ {code}: not found or error\n")
            log.flush()

    driver.quit()

    with open(output_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Barcode", "Product", "Price"])
        writer.writerows(results)

    with open(log_path, "a", encoding="utf-8") as log:
        log.write("\n✅ Scraping complete!\n")
