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
reservation_date = dt.date(2025, 11, 4)  # Exemplo: 4 de novembro de 2025

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
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '予約へ進む')]"))
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
                    match = re.search(r'(\d{4})年(\d{1,2})月', calendar_header)
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
                    from bs4 import BeautifulSoup
                    page_html = driver.page_source
                    soup = BeautifulSoup(page_html, 'html.parser')
                    calendar_cells = soup.find_all("li", class_="calendar-day-cell")
                    print(f"[DEBUG][BS] Encontrou {len(calendar_cells)} células no calendário.")
                    target_data_date = reservation_date.strftime('%Y-%m-%d')
                    clicked = False
                    for idx, cell in enumerate(calendar_cells):
                        cell_classes = cell.get("class", [])
                        cell_text = cell.get_text(strip=True)
                        data_date = cell.get("data-date")
                        print(f"[DEBUG][BS] Célula {idx}: classes={cell_classes}, texto={cell_text}, data-date={data_date}")
                        # Prioridade: data-date igual à data desejada
                        if data_date == target_data_date:
                            print(f"[DEBUG][BS] Clicando na célula {idx} do dia {reservation_date.day} ({data_date}) via Selenium.")
                            selenium_cells = driver.find_elements(By.CLASS_NAME, 'calendar-day-cell')
                            if idx < len(selenium_cells):
                                selenium_cells[idx].click()
                                time.sleep(1)
                                try:
                                    next_btn = driver.find_element(By.ID, 'submit_button')
                                    next_btn.click()
                                    print("Clicou no botão com id 'submit_button'.")
                                except Exception as e:
                                    print("Não conseguiu clicar no botão '次に進む' (Next Step).", e)
                                clicked = True
                                break
                    # Fallback: se não encontrou pelo data-date, tenta por classe e texto
                    if not clicked:
                        # Busca todas as células do dia desejado
                        candidate_idxs = []
                        for idx, cell in enumerate(calendar_cells):
                            cell_classes = cell.get("class", [])
                            cell_text = cell.get_text(strip=True)
                            if cell_text.startswith(str(reservation_date.day)):
                                candidate_idxs.append(idx)
                        # Se houver mais de uma, tenta escolher a do mês correto
                        if candidate_idxs:
                            # Obtém mês/ano do calendário
                            calendar_header = driver.find_element(By.XPATH, "//h3[contains(., '年') and contains(., '月')]").text
                            import re
                            match = re.search(r'(\d{4})年(\d{1,2})月', calendar_header)
                            cal_year = int(match.group(1)) if match else reservation_date.year
                            cal_month = int(match.group(2)) if match else reservation_date.month
                            for idx in candidate_idxs:
                                cell = calendar_cells[idx]
                                # Se o atributo data-date existir, confere mês/ano
                                data_date = cell.get("data-date")
                                if data_date:
                                    try:
                                        y, m, d = map(int, data_date.split('-'))
                                        if y == cal_year and m == cal_month:
                                            print(f"[DEBUG][BS] Fallback: clicando na célula {idx} do dia {reservation_date.day} ({data_date}) do mês correto via Selenium.")
                                            selenium_cells = driver.find_elements(By.CLASS_NAME, 'calendar-day-cell')
                                            if idx < len(selenium_cells):
                                                selenium_cells[idx].click()
                                                time.sleep(1)
                                                try:
                                                    next_btn = driver.find_element(By.ID, 'submit_button')
                                                    next_btn.click()
                                                    print("Clicou no botão com id 'submit_button'.")
                                                except Exception as e:
                                                    print("Não conseguiu clicar no botão '次に進む' (Next Step).", e)
                                                clicked = True
                                                break
                                    except Exception:
                                        pass
                                else:
                                    # Se não tem data-date, identifica o início do mês atual
                                    # Busca o índice da primeira célula sem 'calendar-day-other-month'
                                    first_current_month_idx = None
                                    for i, c in enumerate(calendar_cells):
                                        c_classes = c.get("class", [])
                                        if 'calendar-day-other-month' not in c_classes:
                                            first_current_month_idx = i
                                            break
                                    # Nova lógica: se o dia for > 25, clica na segunda célula; se < 7, clica na primeira
                                    candidate_idxs = []
                                    for idx, cell in enumerate(calendar_cells):
                                        cell_text = cell.get_text(strip=True)
                                        if cell_text.startswith(str(reservation_date.day)):
                                            candidate_idxs.append(idx)
                                    print(f"[DEBUG][BS] Indices candidatos para o dia {reservation_date.day}: {candidate_idxs}")
                                    selenium_cells = driver.find_elements(By.CLASS_NAME, 'calendar-day-cell')
                                    if candidate_idxs:
                                        if reservation_date.day > 25 and len(candidate_idxs) > 1:
                                            target_idx = candidate_idxs[1]
                                            print(f"[DEBUG][BS] Dia > 25, clicando na segunda célula de índice {target_idx}.")
                                        else:
                                            target_idx = candidate_idxs[0]
                                            print(f"[DEBUG][BS] Dia < 7 ou padrão, clicando na primeira célula de índice {target_idx}.")
                                        if target_idx < len(selenium_cells):
                                            selenium_cells[target_idx].click()
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
                            print(f"[DEBUG][BS] Não encontrou célula do dia {reservation_date.day} do mês correto.")
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
