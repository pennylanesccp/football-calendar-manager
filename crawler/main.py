import os
import csv
import time
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def log(message, level='INFO'):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] [{level}] {message}")

def initialize_driver():
    log("Iniciando o WebDriver.")
    options = Options()
    # options.add_argument('--headless')  # Descomente esta linha para executar em modo headless
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)
    return driver

def accept_cookies(driver):
    try:
        log("Verificando a presença do pop-up de cookies.")
        accept_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Aceitar")]'))
        )
        accept_button.click()
        log("Pop-up de cookies aceito.")
    except:
        log("Pop-up de cookies não encontrado ou já aceito.")

def write_matches_to_csv(matches, csv_filename):
    log(f"Escrevendo os dados no arquivo CSV: {csv_filename}")
    with open(csv_filename, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ['Campeonato', 'Data', 'Hora', 'Time Casa', 'Time Fora']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for match in matches:
            writer.writerow(match)
    log("Dados escritos com sucesso no arquivo CSV.", level='SUCCESS')

def process_matches(driver):
    matches = []
    try:
        # Aguarda até que os elementos das partidas estejam presentes
        WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.sc-bdnxRM'))
        )

        # Encontra todos os blocos de competições
        competition_blocks = driver.find_elements(By.CSS_SELECTOR, 'div.sc-bdnxRM')

        if not competition_blocks:
            log("Nenhum bloco de competição encontrado.", level='ERROR')
            return matches

        for competition_block in competition_blocks:
            try:
                # Nome da competição
                competition_name = competition_block.find_element(By.CSS_SELECTOR, 'div.sc-jbKcbu a').text.strip()
            except Exception as e:
                competition_name = 'Unknown'
                log(f"Erro ao obter o nome da competição: {e}", level='ERROR')

            match_elements = competition_block.find_elements(By.CSS_SELECTOR, 'a[href*="/match/"]')

            for match_element in match_elements:
                try:
                    datetime_element = match_element.find_element(By.CSS_SELECTOR, 'div.sc-dkPtRN bdi')
                    date_text = datetime_element.text.strip()

                    time_element = match_element.find_element(By.CSS_SELECTOR, 'div.sc-hBxehG bdi')
                    time_text = time_element.text.strip()

                    # Filtra apenas partidas futuras (ignora "FT" e horários vazios)
                    if time_text == 'FT' or not time_text:
                        continue

                    # Times
                    teams = match_element.find_elements(By.CSS_SELECTOR, 'div.sc-iNqMzA bdi')
                    if len(teams) < 2:
                        continue
                    home_team = teams[0].text.strip()
                    away_team = teams[1].text.strip()

                    match_data = {
                        'Campeonato': competition_name,
                        'Data': date_text,
                        'Hora': time_text,
                        'Time Casa': home_team,
                        'Time Fora': away_team
                    }

                    # Evitar duplicações
                    if match_data not in matches:
                        matches.append(match_data)
                        log(f"Jogo encontrado: {home_team} x {away_team} no dia {date_text} às {time_text} ({competition_name})")
                    else:
                        log(f"Partida duplicada ignorada: {home_team} x {away_team} no dia {date_text} às {time_text} ({competition_name})")

                except Exception as e:
                    log(f"Erro ao processar uma partida: {e}\n{traceback.format_exc()}", level='ERROR')

    except Exception as e:
        log(f"Erro ao processar partidas: {e}\n{traceback.format_exc()}", level='ERROR')

    return matches

def main():
    driver = initialize_driver()
    try:
        url = 'https://www.sofascore.com/team/football/corinthians/1957'
        log(f"Acessando a URL: {url}")
        driver.get(url)

        accept_cookies(driver)

        log("Aguardando o carregamento do conteúdo das partidas.")
        matches = process_matches(driver)

        # Escrever os dados no arquivo CSV
        csv_filename = 'corinthians_upcoming_matches.csv'
        write_matches_to_csv(matches, csv_filename)

    except Exception as e:
        log(f"Erro durante a execução do script: {e}\n{traceback.format_exc()}", level='ERROR')

    finally:
        log("Encerrando o WebDriver e fechando o navegador.", level='INFO')
        driver.quit()

if __name__ == "__main__":
    main()
