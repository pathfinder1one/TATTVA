import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def launch_browser() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,900")
    driver = webdriver.Chrome(service=Service(), options=options)
    driver.set_page_load_timeout(30)
    return driver


def type_solution(driver: webdriver.Chrome, problem_url: str, code: str) -> bool:
    driver.get(problem_url)
    try:
        editor = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[class*='CodeMirror'], .CodeMirror textarea, textarea"))
        )
        editor.click()
        for _ in range(3):
            editor.send_keys(Keys.CONTROL, "a")
        editor.send_keys(Keys.DELETE)
        for char in code:
            editor.send_keys(char)
            time.sleep(0.01)
        return True
    except Exception:
        return False


def execute_code(driver: webdriver.Chrome) -> dict:
    try:
        run_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class*='run'], button:has(text(\\'Run\\')), button:has(text(\\'Run Code\\'))"))
        )
        run_btn.click()
        time.sleep(5)
        result_elem = driver.find_element(By.CSS_SELECTOR, "div[class*='result'], div[class*='output'], .OutputContainer")
        status = "success"
        text = result_elem.text
        if "error" in text.lower() or "exception" in text.lower():
            status = "error"
        return {"status": status, "output": text}
    except Exception as e:
        return {"status": "error", "output": str(e)}