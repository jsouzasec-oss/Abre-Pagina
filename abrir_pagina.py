from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
import datetime as dt
from bs4 import BeautifulSoup

# Caminho para o ChromeDriver
CHROMEDRIVER_PATH = r'./chromedriver.exe'  # Atualize se necessário



# URLs disponíveis
URL_OSAKA = 'https://osaka.pokemon-cafe.jp/'
URL_TOKYO = 'https://reserve.pokemon-cafe.jp/'

# Escolha qual URL usar
URL = URL_TOKYO  # Altere para URL_TOKYO se quiser usar o outro site


num_of_guests = '2'  # Número de convidados a selecionar
# Data da reserva (formato: YYYY-MM-DD)
reservation_date = dt.date(2025, 11, 4)  # Exemplo: 6 de novembro de 2025

# Dados do formulário de reserva
user_name = 'Rodrigo Azevedo'
user_name_kana = user_name  # name_kana igual ao name
user_phone = '5521972733483'
user_email = 'rodrigo4zevedo@gmail.com'

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

            time.sleep(2)
            #print(driver.page_source)
        except Exception as e:
            print("Não encontrou ou não conseguiu clicar em '同意して進む'.", e)

        # Verifica se está em Human Verification pelo id 'captcha-container'
        def is_human_verification_page(driver):
            try:
                return driver.find_element(By.ID, 'captcha-container') is not None
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
            if driver.current_url == URL_OSAKA + 'reserve/auth_confirm' or driver.current_url == URL_TOKYO + 'reserve/auth_confirm':
                proceed_btn = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '予約へ進む')]") )
                )
                proceed_btn.click()
                print("Clicou em '予約へ進む'.")
        except Exception as e:
            print("Não encontrou ou não conseguiu clicar em '予約へ進む'.", e)

        # Se estiver na página de seleção de convidados, seleciona o número e clica no dia do calendário
        try:
            if driver.current_url == URL_OSAKA + 'reserve/step1' or driver.current_url == URL_TOKYO + 'reserve/step1':
                from selenium.webdriver.support.ui import Select
                select = Select(driver.find_element(By.NAME, 'guest'))
                select.select_by_index(num_of_guests)
                print(f"Selecionou {num_of_guests} convidados no elemento 'guest'.")
                time.sleep(2)
                # Espera o calendário aparecer
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'calendar-day-cell'))
                )

                # Avança o calendário até o mês/ano desejado
                print(f"[DEBUG] Data desejada: {reservation_date}")
                import re
                while True:
                    calendar_header = driver.find_element(By.XPATH, "//h3[contains(., '年') and contains(., '月')]").text
                    match = re.search(r'(\d{4})年(\d{1,2})月', calendar_header)
                    print(f"[DEBUG] Header do calendário: {calendar_header}")
                    if match:
                        print(f"[DEBUG] Mês/ano atual: {match.group(1)}-{match.group(2)}")
                        cal_year = int(match.group(1))
                        cal_month = int(match.group(2))
                        if cal_year == reservation_date.year and cal_month == reservation_date.month:
                            break
                        print("Mês do calendário diferente do desejado. Indo para o próximo mês...")
                        next_month_btns = driver.find_elements(By.CLASS_NAME, 'calendar-pager')
                        found = False
                        for btn in next_month_btns:
                            if '(Next Month)' in btn.text:
                                btn.click()
                                found = True
                                print("Clicou no botão 'Next Month'.")
                                time.sleep(3)
                                break
                        if not found:
                            print("Não encontrou o botão 'Next Month' com o texto esperado.")
                            break
                    else:
                        print("Não foi possível identificar o mês do calendário.")
                        break
                import re
                while True:
                    calendar_header = driver.find_element(By.XPATH, "//h3[contains(., '年') and contains(., '月')]" ).text
                    match = re.search(r'(\d{4})年(\d{1,2})月S', calendar_header)
                    if match:
                        cal_year = int(match.group(1))
                        cal_month = int(match.group(2))
                        if cal_year == reservation_date.year and cal_month == reservation_date.month:
                            break
                        print("Mês do calendário diferente do desejado. Indo para o próximo mês...")
                        next_month_btns = driver.find_elements(By.CLASS_NAME, 'calendar-pager')
                        found = False
                        for btn in next_month_btns:
                            if '(Next Month)' in btn.text:
                                btn.click()
                                found = True
                                print("Clicou no botão 'Next Month'.")
                                time.sleep(3)
                                break
                        if not found:
                            print("Não encontrou o botão 'Next Month' com o texto esperado.")
                            break
                    else:
                        print("Não foi possível identificar o mês do calendário.")
                        break

                # Agora sim, clica no dia correspondente à variável reservation_date.day
                try:
                    day_cells = driver.find_elements(By.XPATH, f"//li[contains(@class, 'calendar-day-cell') and .//div[text()='{reservation_date.day}']]")
                    print(f"[DEBUG] Encontrou {len(day_cells)} células para o dia {reservation_date.day}.")
                    clicked = False
                    for idx, cell in enumerate(day_cells):
                        cell_classes = cell.get_attribute('class')
                        cell_text = cell.text
                        print(f"[DEBUG] Célula {idx}: classes={cell_classes}, texto={cell_text}")
                        if 'calendar-day-other-month' not in cell_classes:
                            print(f"[DEBUG] Clicando na célula {idx} do dia {reservation_date.day}.")
                            cell.click()
                            time.sleep(1)
                            try:
                                next_btn = driver.find_element(By.ID, 'submit_button')
                                next_btn.click()
                                print("Clicou no botão com id 'submit_button'.")
                            except Exception as e:
                                print("Não conseguiu clicar no botão '次に進む' (Next Step).", e)
                            clicked = True
                            break
                    if not clicked:
                        print(f"[DEBUG] Não encontrou célula do dia {reservation_date.day} do mês correto.")
                except Exception as e:
                    print(f"Não conseguiu clicar no dia {reservation_date.day} do calendário.", e)
        except Exception as e:
            print(f"Não conseguiu selecionar {num_of_guests} convidados no elemento 'guest'.", e)

        # Se estiver na página de seleção de horário (step3), tenta clicar em um horário disponível
        try:
            while 'step2' in driver.current_url:
                time.sleep(2)
                # Verifica se está em Human Verification pelo id 'captcha-container'
                try:
                    if driver.find_elements(By.ID, 'captcha-container'):
                        log_human_verification()
                        print("Aguardando interação humana: página de verificação detectada.")
                        while driver.find_elements(By.ID, 'captcha-container'):
                            time.sleep(2)
                        print("Verificação humana resolvida, voltando à busca de horários.")
                        continue
                except Exception as e:
                    print(f"Erro ao verificar Human Verification: {e}")

                try:
                    available_slots = driver.find_elements(By.XPATH, "//div[@class='status level-left' and text()='Available']")
                    if available_slots:
                        # Clica na célula pai do primeiro horário disponível
                        slot_cell = available_slots[0].find_element(By.XPATH, "..")
                        slot_cell.click()
                        print("Clicou em um horário disponível.")
                        break
                    else:
                        print("Nenhum horário disponível encontrado. Atualizando a página...")
                        with open('log.txt', 'a', encoding='utf-8') as f:
                            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            f.write(f"[{now}] Página de horários atualizada em step2.\n")
                        driver.refresh()
                except Exception as e:
                    print(f"Erro ao buscar horários disponíveis: {e}")
        except Exception as e:
            print(f"Erro ao tentar selecionar horário disponível: {e}")

        # Se estiver na página de preenchimento de dados (step3), preenche e envia o formulário
        try:
            if driver.current_url == URL_OSAKA + 'reserve/step3' or driver.current_url == URL_TOKYO + 'reserve/step3':
                time.sleep(2)
                driver.find_element(By.ID, 'name').send_keys(user_name)
                driver.find_element(By.ID, 'name_kana').send_keys(user_name_kana)
                driver.find_element(By.ID, 'phone_number').send_keys(user_phone)
                driver.find_element(By.ID, 'email').send_keys(user_email)
                print("Preencheu os dados do formulário.")
                time.sleep(1)
                driver.find_element(By.ID, 'submit_button').click()
                print("Clicou no botão de envio do formulário.")
        except Exception as e:
            print(f"Erro ao preencher ou enviar o formulário: {e}")

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
