from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


# Path to your ChromeDriver executable
CHROMEDRIVER_PATH = r'./chromedriver.exe'  # Update this path if needed
num_of_guests = 2  # Example: number of guests to select
day_of_month = '2025-11-01'  # Data de 1 de novembro de 2025

# URL to open
URL = 'https://reserve.pokemon-cafe.jp/reserve/step1'

SEARCH_TEXT = 'This site is congested due to heavy access.'  # Texto a ser procurado
TIMEOUT = 30  # Tempo máximo de espera em segundos

try:
    chrome_options = Options()
    # chrome_options.add_argument('--headless=new')  # Ative se quiser modo headless
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(URL)
  
    found = False
    start_time = time.time()
    while time.time() - start_time < TIMEOUT:
        if SEARCH_TEXT in driver.page_source:
            select = Select(driver.find_element(By.NAME, 'guest'))
            select.select_by_index(num_of_guests)
            
            # Wait for the page to load and elements to be ready
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".calendar-day-cell"))
            )
            # Check if the updated page indicates availability
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # Find all calendar-day-cell elements
            calendar_cells = soup.find_all("li", class_="calendar-day-cell")

            #    Check each calendar cell for availability
            available_slots = []
            for cell in calendar_cells:
                if "full" not in cell.text.lower() and "n/a" not in cell.text.lower():
                    available_slots.append(cell.text.strip())

            if available_slots:
                driver.find_element(By.XPATH, "//*[contains(text(), " + str(day_of_month) + ")]").click()
                driver.find_element(By.XPATH, "//*[@class='button']").click()
            else:
                print("No available slots found.")
            
            driver.find_element(By.XPATH, "//*[contains(text(), '次の月を見る')]").click()
            print(f"Texto '{SEARCH_TEXT}' encontrado! Atualizando o navegador...")
            found = True
            driver.refresh()
        time.sleep(1)

    if not found:
        input("Pressione Enter para fechar o navegador...")
    driver.quit()
except Exception as e:
    print(f"Ocorreu um erro: {e}")
    input("Pressione Enter para sair...")
