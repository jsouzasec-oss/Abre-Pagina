from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Caminho para o ChromeDriver
CHROMEDRIVER_PATH = r'./chromedriver.exe'  # Atualize se necessário

# URL para abrir
URL = 'https://osaka.pokemon-cafe.jp/'

num_of_guests = '2'  # Número de convidados a selecionar
day_of_month = '5'  # Data de 1 de novembro de 2025

def log_restart():
    with open('log.txt', 'a', encoding='utf-8') as f:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{now}] Voltamos para a etapa inicial da reserva.\n")

def log_human_verification():
    with open('log.txt', 'a', encoding='utf-8') as f:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(f"[{now}] Página de Human Verification detectada.\n")

def is_on_initial_page(driver):
    # Verifica se está na página inicial pelo título ou outro elemento único
    return 'ポケモンカフェ' in driver.title or 'Pokemon Cafe' in driver.title

try:
    chrome_options = Options()
    # chrome_options.add_argument('--headless=new')  # Ative para modo headless
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    while True:
        driver.get(URL)

        # Verifica se a página está congestionada em qualquer momento do processo
        def check_congestion():
            if 'The site is congested due to heavy access.' in driver.page_source:
                print("Site congestionado. Registrando no log.txt e reiniciando o processo...")
                with open('log.txt', 'a', encoding='utf-8') as f:
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    f.write(f"[{now}] Site congestionado detectado. Processo reiniciado.\n")
                return True
            return False

        if check_congestion():
            continue

        # Espera o botão "Agree to terms" aparecer e clica
        try:
            agree_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Agree to terms')]") )
            )
            agree_btn.click()
            print("Clicou em 'Agree to terms'.")
        except Exception as e:
            print("Não encontrou ou não conseguiu clicar em 'Agree to terms'.", e)

        # Espera o botão "同意して進む" aparecer e clica
        try:
            go_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '同意して進む')]") )
            )
            go_btn.click()
            print("Clicou em '同意して進む'.")
        except Exception as e:
            print("Não encontrou ou não conseguiu clicar em '同意して進む'.", e)

        # Verifica se está em Human Verification pelo id do botão captcha
        def is_human_verification_page(driver):
            try:
                return driver.find_element(By.ID, 'amzn-captcha-verify-button') is not None
            except:
                return False

        try:
            if is_human_verification_page(driver):
                log_human_verification()
            while is_human_verification_page(driver):
                print("Aguardando interação humana: página de verificação detectada.")
                time.sleep(2)
        except Exception as e:
            print(f"Erro ao verificar página de Human Verification: {e}")

        # Se estiver na página de confirmação de autenticação, tenta clicar no botão '予約へ進む'
        try:
            if driver.current_url == 'https://osaka.pokemon-cafe.jp/reserve/auth_confirm':
                proceed_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '予約へ進む')]") )
                )
                proceed_btn.click()
                print("Clicou em '予約へ進む'.")
        except Exception as e:
            print("Não encontrou ou não conseguiu clicar em '予約へ進む'.", e)

        # Se estiver na página de seleção de convidados, seleciona 4 no elemento 'guest'
        try:
            if driver.current_url == 'https://osaka.pokemon-cafe.jp/reserve/step1':
                from selenium.webdriver.support.ui import Select
                select = Select(driver.find_element(By.NAME, 'guest'))
                select.select_by_index(num_of_guests)
                #driver.find_element(By.XPATH, "//*[contains(text(), '次の月を見る')]").click()
                print(f"Selecionou {num_of_guests} convidados no elemento 'guest'.")
                
                # Wait for the page to load and elements to be ready
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".calendar-day-cell"))
                )

                # Clica para ir para o proximo mes
                driver.find_element(By.XPATH, "//*[contains(text(), '次の月を見る')]").click()
                print("Clicou em '次の月を見る' para ver o próximo mês.")              
                
                 # Check if the updated page indicates availability
                soup = BeautifulSoup(driver.page_source, "html.parser")
                # Find all calendar-day-cell elements
                calendar_cells = soup.find_all("li", class_="calendar-day-cell")

                # Check each calendar cell for availability
                available_slots = []
                for cell in calendar_cells:
                    if "full" in cell.text.lower():
                        available_slots.append(cell.text.strip())

                if available_slots:
                    driver.find_element(By.XPATH, "//*[contains(text(), " + str(day_of_month) + ")]").click()
                    driver.find_element(By.XPATH, "//*[@class='button']").click()
        
        except Exception as e:
            print(f"Não conseguiu selecionar {num_of_guests} convidados no elemento 'guest'.", e)

        # Aguarda um tempo para ver se volta para a página inicial
        time.sleep(5)
        try:
            if is_on_initial_page(driver):
                print("Voltamos para a etapa inicial da reserva. Registrando no log.txt...")
                log_restart()
                continue  # Reinicia o processo
            else:
                input("Pressione Enter para fechar o navegador...")
                break
        except Exception as e:
            print(f"Erro ao verificar página inicial: {e}")
    driver.quit()
except Exception as e:
    print(f"Ocorreu um erro: {e}")
    input("Pressione Enter para sair...")
