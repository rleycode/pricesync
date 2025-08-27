import os
import time
import logging
from typing import Optional, List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import Config

logger = logging.getLogger(__name__)

class MetallprofilScraper:

    def __init__(self):
        self.login = Config.METALLPROFIL_LOGIN
        self.password = Config.METALLPROFIL_PASSWORD
        self.base_url = Config.METALLPROFIL_URL
        self.download_dir = Config.DOWNLOAD_DIR
        self.timeout = Config.BROWSER_TIMEOUT
        self.driver = None
        
        # Создаем директорию для загрузок
        os.makedirs(self.download_dir, exist_ok=True)
    
    def _setup_driver(self) -> webdriver.Chrome:

        chrome_options = Options()
        
        if Config.BROWSER_HEADLESS:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Настройка загрузок
        prefs = {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            return driver
        except Exception as e:
            logger.error(f"Ошибка при создании WebDriver: {e}")
            raise
    
    def login_to_site(self) -> bool:

        try:
            self.driver = self._setup_driver()
            
            logger.info("Переход на страницу входа")
            self.driver.get(f"{self.base_url}/login")
            
            # Ждем загрузки формы входа
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Находим поля логина и пароля
            login_field = wait.until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            # Вводим данные
            logger.info("Ввод учетных данных")
            login_field.clear()
            login_field.send_keys(self.login)
            
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Нажимаем кнопку входа
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Ждем успешного входа
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "user-menu"))
            )
            
            logger.info("Успешный вход в личный кабинет")
            return True
            
        except TimeoutException:
            logger.error("Таймаут при входе в систему")
            return False
        except NoSuchElementException as e:
            logger.error(f"Не найден элемент на странице: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при входе в систему: {e}")
            return False
    
    def navigate_to_pricelist(self) -> bool:

        try:
            logger.info("Переход на страницу прайс-листа")
            
            # Прямой переход на страницу прайс-листа
            price_url = f"{self.base_url}/price/"
            self.driver.get(price_url)
            
            # Ждем загрузки страницы
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Проверяем, что страница загрузилась
            wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Дополнительная проверка на наличие контента прайс-листа
            try:
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.pdf')]")),
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'прайс')]")),
                        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Прайс')]")),
                        EC.presence_of_element_located((By.CLASS_NAME, "price-list")),
                        EC.presence_of_element_located((By.CLASS_NAME, "download"))
                    )
                )
            except TimeoutException:
                logger.warning("Не найдены элементы прайс-листа, но страница загружена")
            
            logger.info("Успешный переход на страницу прайс-листа")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при переходе к прайс-листу: {e}")
            return False
    
    def download_pricelist_pdf(self) -> Optional[str]:

        try:
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Специфичные селекторы для Металлпрофиль
            pdf_selectors = [
                # Ссылки на get_file.php (динамические ссылки)
                "//a[contains(@href, 'get_file.php')]",
                "//a[contains(@href, '/upload/prices/')]",
                # Общие селекторы для PDF
                "//a[contains(@href, '.pdf')]",
                # Текстовые ссылки
                "//a[contains(text(), 'Прайс-лист')]",
                "//a[contains(text(), 'прайс-лист')]",
                "//a[contains(text(), 'основной')]",
                "//a[contains(text(), 'Скачать')]",
                # Кнопки
                "//button[contains(text(), 'Скачать')]",
                "//input[@type='button' and contains(@value, 'Скачать')]"
            ]
            
            pdf_link = None
            found_selector = None
            
            for selector in pdf_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        # Берем первый найденный элемент
                        pdf_link = elements[0]
                        found_selector = selector
                        logger.info(f"Найдена ссылка на PDF: {found_selector}")
                        break
                except Exception as e:
                    logger.debug(f"Селектор {selector} не сработал: {e}")
                    continue
            
            if not pdf_link:
                logger.error("Не найдена ссылка на PDF файл")
                # Попробуем найти все ссылки на странице для отладки
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                logger.debug(f"Найдено {len(all_links)} ссылок на странице")
                for link in all_links[:10]:  # Показываем первые 10 ссылок
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    logger.debug(f"Ссылка: {href} | Текст: {text}")
                return None
            
            # Получаем информацию о ссылке
            href = pdf_link.get_attribute('href')
            link_text = pdf_link.text.strip()
            
            logger.info(f"Найдена ссылка: {href}")
            logger.info(f"Текст ссылки: {link_text}")
            
            # Определяем имя файла
            if 'file_name=' in href:
                # Извлекаем имя файла из параметра URL
                import urllib.parse
                parsed_url = urllib.parse.urlparse(href)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'file_name' in query_params:
                    filename = urllib.parse.unquote(query_params['file_name'][0])
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
                else:
                    filename = f"metallprofil_pricelist_{int(time.time())}.pdf"
            else:
                filename = f"metallprofil_pricelist_{int(time.time())}.pdf"
            
            # Очищаем имя файла от недопустимых символов
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            
            logger.info(f"Начало скачивания файла: {filename}")
            
            # Кликаем по ссылке
            self.driver.execute_script("arguments[0].click();", pdf_link)
            
            # Ждем завершения загрузки
            file_path = os.path.join(self.download_dir, filename)
            
            # Ждем появления файла (максимум 60 секунд)
            for i in range(60):
                # Проверяем точное имя файла
                if os.path.exists(file_path):
                    logger.info(f"Файл успешно скачан: {file_path}")
                    return file_path
                
                # Проверяем файлы с похожими именами
                if os.path.exists(self.download_dir):
                    for existing_file in os.listdir(self.download_dir):
                        if existing_file.endswith('.pdf') and 'metallprofil' in existing_file.lower():
                            existing_path = os.path.join(self.download_dir, existing_file)
                            # Проверяем, что файл был создан недавно (последние 2 минуты)
                            if time.time() - os.path.getctime(existing_path) < 120:
                                logger.info(f"Найден скачанный файл: {existing_path}")
                                return existing_path
                
                time.sleep(1)
                if i % 10 == 0:  # Логируем каждые 10 секунд
                    logger.info(f"Ожидание скачивания... ({i}/60 сек)")
            
            # Если файл не появился, ищем последний скачанный PDF
            if os.path.exists(self.download_dir):
                pdf_files = [f for f in os.listdir(self.download_dir) if f.endswith('.pdf')]
                if pdf_files:
                    latest_file = max(pdf_files, key=lambda x: os.path.getctime(os.path.join(self.download_dir, x)))
                    file_path = os.path.join(self.download_dir, latest_file)
                    logger.info(f"Найден последний скачанный PDF файл: {file_path}")
                    return file_path
            
            logger.error("Файл не был скачан в течение 60 секунд")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при скачивании PDF: {e}")
            return None
    
    def find_pricelist_links(self) -> List[Dict[str, str]]:

        links = []
        
        try:
            # Находим все ссылки на странице
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            
            for link in all_links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    
                    if not href:
                        continue
                    
                    # Проверяем, является ли это ссылкой на прайс-лист
                    is_pricelist = any([
                        'get_file.php' in href and 'prices' in href,
                        '.pdf' in href.lower(),
                        'прайс' in text.lower(),
                        'price' in href.lower(),
                        'основной' in text.lower()
                    ])
                    
                    if is_pricelist:
                        link_info = {
                            'href': href,
                            'text': text,
                            'element': link
                        }
                        links.append(link_info)
                        logger.debug(f"Найдена потенциальная ссылка на прайс: {href} | {text}")
                
                except Exception as e:
                    logger.debug(f"Ошибка при обработке ссылки: {e}")
                    continue
            
            logger.info(f"Найдено {len(links)} потенциальных ссылок на прайс-листы")
            return links
            
        except Exception as e:
            logger.error(f"Ошибка при поиске ссылок на прайс-листы: {e}")
            return []
    
    def download_pdf_by_direct_url(self, pdf_url: str) -> Optional[str]:

        try:
            import requests
            
            logger.info(f"Попытка скачивания PDF по прямой ссылке: {pdf_url}")
            
            # Получаем cookies из текущей сессии браузера
            cookies = {}
            for cookie in self.driver.get_cookies():
                cookies[cookie['name']] = cookie['value']
            
            # Скачиваем файл
            response = requests.get(pdf_url, cookies=cookies, stream=True)
            response.raise_for_status()
            
            # Определяем имя файла
            filename = f"metallprofil_direct_{int(time.time())}.pdf"
            if 'file_name=' in pdf_url:
                import urllib.parse
                parsed_url = urllib.parse.urlparse(pdf_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'file_name' in query_params:
                    filename = urllib.parse.unquote(query_params['file_name'][0])
                    if not filename.endswith('.pdf'):
                        filename += '.pdf'
            
            # Очищаем имя файла
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
            
            file_path = os.path.join(self.download_dir, filename)
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"PDF успешно скачан: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Ошибка при прямом скачивании PDF: {e}")
            return None
    
    def scrape_pricelist(self) -> Optional[str]:

        try:
            logger.info("Начало процесса получения прайс-листа Металлпрофиль")
            
            # Вход в систему
            if not self.login_to_site():
                return None
            
            # Переход к прайс-листу
            if not self.navigate_to_pricelist():
                return None
            
            # Ищем все возможные ссылки на прайс-листы
            pricelist_links = self.find_pricelist_links()
            
            if not pricelist_links:
                logger.error("Не найдено ссылок на прайс-листы")
                return None
            
            # Пробуем скачать файл разными способами
            file_path = None
            
            # Способ 1: Стандартное скачивание через клик
            logger.info("Попытка стандартного скачивания...")
            file_path = self.download_pricelist_pdf()
            
            if file_path:
                return file_path
            
            # Способ 2: Прямое скачивание по ссылкам
            logger.info("Попытка прямого скачивания по найденным ссылкам...")
            for link_info in pricelist_links:
                href = link_info['href']
                if 'get_file.php' in href or '.pdf' in href:
                    logger.info(f"Попытка скачивания: {href}")
                    file_path = self.download_pdf_by_direct_url(href)
                    if file_path:
                        return file_path
            
            # Способ 3: Клик по каждой найденной ссылке
            logger.info("Попытка клика по найденным ссылкам...")
            for i, link_info in enumerate(pricelist_links):
                try:
                    logger.info(f"Клик по ссылке {i+1}: {link_info['text']} | {link_info['href']}")
                    element = link_info['element']
                    
                    # Прокручиваем к элементу
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(1)
                    
                    # Кликаем
                    self.driver.execute_script("arguments[0].click();", element)
                    
                    # Ждем немного и проверяем, появился ли файл
                    time.sleep(5)
                    
                    # Проверяем загрузки
                    if os.path.exists(self.download_dir):
                        pdf_files = [f for f in os.listdir(self.download_dir) if f.endswith('.pdf')]
                        if pdf_files:
                            latest_file = max(pdf_files, key=lambda x: os.path.getctime(os.path.join(self.download_dir, x)))
                            latest_path = os.path.join(self.download_dir, latest_file)
                            # Проверяем, что файл свежий (создан в последние 30 секунд)
                            if time.time() - os.path.getctime(latest_path) < 30:
                                logger.info(f"Файл успешно скачан через клик: {latest_path}")
                                return latest_path
                
                except Exception as e:
                    logger.warning(f"Ошибка при клике по ссылке {i+1}: {e}")
                    continue
            
            logger.error("Все способы скачивания не сработали")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка при получении прайс-листа: {e}")
            return None
        finally:
            self.close()
    
    def close(self):
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Браузер закрыт")
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {e}")
    
    def test_connection(self) -> bool:

        try:
            self.driver = self._setup_driver()
            self.driver.get(self.base_url)
            
            # Проверяем, что страница загрузилась
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info("Сайт Металлпрофиль доступен")
            return True
            
        except Exception as e:
            logger.error(f"Сайт Металлпрофиль недоступен: {e}")
            return False
        finally:
            self.close()
