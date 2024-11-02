import concurrent.futures
import json
import logging
import os
import threading
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import cloudinary
import cloudinary.uploader
import cloudinary.api
from dotenv import load_dotenv
import requests
from requests.exceptions import ProxyError, Timeout, RequestException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

app = Flask(__name__)
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name="dm7uq1adt",
    api_key="246721327163695",
    api_secret="Pozr913oXcnPC6P4JrsSjkuA6oA"
)

def is_valid_proxy(proxy):
    try:
        response = requests.get('https://www.google.com', proxies={"http": proxy, "https": proxy}, timeout=5)
        if response.status_code == 200:
            logger.info("Proxy is valid: %s", proxy)
            return True
        else:
            logger.warning("Proxy returned non-200 status code: %d", response.status_code)
            return False
    except ProxyError:
        logger.error("ProxyError: The proxy is not valid or not reachable.")
        return False
    except Timeout:
        logger.error("Timeout: The proxy timed out.")
        return False
    except RequestException as e:
        logger.error("RequestException: %s", str(e))
        return False

def login_to_linkedin(driver, username, password):
    driver.get("https://www.linkedin.com/login")
    email_element = driver.find_element(By.ID, "username")
    email_element.send_keys(username)
    password_element = driver.find_element(By.ID, "password")
    password_element.send_keys(password)
    sign_in_button = driver.find_element(By.XPATH, "//button[@type='submit']")
    sign_in_button.click()
    time.sleep(5)

class ScrapeException(Exception):
    pass

class Scrapper:
    COOKIES_FILE = "cookies.json"

    def __init__(self, proxy=None, username=None, password=None, stop_event=None):
        logger.info("Initializing Scrapper")
        self.chrome_options = Options()

        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
        self.chrome_options.add_argument('--log-level 3')
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_argument("--lang=en-US,en;q=0.9")
        # self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        chrome_service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=chrome_service, options=self.chrome_options)

        self.stop_event = stop_event or threading.Event()

        if os.path.exists(self.COOKIES_FILE):
            self.load_cookies()
            logger.info("Loaded cookies from previous session.")
            # Check if cookies are valid by navigating to a LinkedIn page
            self.driver.get("https://www.linkedin.com/")
            time.sleep(2)
            if "/login" in self.driver.current_url:
                logger.warning("Cookies are not valid, attempting login.")
                if username and password:
                    login_to_linkedin(self.driver, username, password)
                    self.save_cookies()
                else:
                    logger.error("No LinkedIn credentials provided and cookies are invalid.")
                    raise ScrapeException("No valid cookies found, and no credentials provided.")
            else:
                logger.info("Cookies are valid, skipping login.")
        else:
            if username and password:
                login_to_linkedin(self.driver, username, password)
                self.save_cookies()
            else:
                logger.warning("No LinkedIn credentials provided; attempting to scrape without login.")

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        """Clean up resources by closing the display and browser."""
        if hasattr(self, 'display'):
            self.display.stop()
        if hasattr(self, 'driver'):
            self.driver.quit()

    def save_cookies(self):
        logger.info("Saving cookies...")
        cookies = self.driver.get_cookies()
        with open(self.COOKIES_FILE, 'w') as f:
            json.dump(cookies, f)
        logger.info("Cookies saved successfully.")

    def load_cookies(self):
        self.driver.get("https://www.linkedin.com")
        with open(self.COOKIES_FILE, 'r') as file:
            cookies = json.load(file)
            for cookie in cookies:
                if "linkedin.com" in cookie['domain']:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.warning(f"Failed to add cookie: {cookie['name']} - {e}")
        logger.info("Cookies loaded successfully.")

    def take_full_page_screenshot(self):
        logger.info("Taking full-page screenshot")
        original_size = self.driver.get_window_size()
        total_width = self.driver.execute_script("return document.body.scrollWidth")
        total_height = self.driver.execute_script("return document.body.scrollHeight")
        self.driver.set_window_size(total_width, total_height)
        time.sleep(2)
        screenshot = self.driver.get_screenshot_as_png()
        self.driver.set_window_size(original_size['width'], original_size['height'])
        logger.info("Screenshot taken successfully")
        return screenshot

    def upload_to_cloudinary(self, image_data):
        logger.info("Uploading screenshot to Cloudinary")
        upload_result = cloudinary.uploader.upload(image_data, folder="scraper_screenshots/")
        logger.info("Screenshot uploaded successfully: %s", upload_result['secure_url'])
        return upload_result['secure_url']
    
    def scrape(self, url) -> dict:
        try:
            logger.info("Starting scrape for URL: %s", url)
            self.driver.get(url)
            time.sleep(3)

            tries = 0
            while self.driver.current_url != url:
                if self.stop_event.is_set():
                    logger.info("Stop event set, terminating this scrape attempt")
                    return None  # Return None to indicate the process was stopped

                logger.warning("Redirected to login page, retrying... Attempt: %d", tries + 1)
                if tries > 50:
                    logger.error("Exceeded maximum retry attempts. Scraping failed.")
                    raise ScrapeException("Could not scrape page. \nRequest timed out, Please try with proxy as LinkedIn is blocking your request.")

                self.driver.get(url)
                time.sleep(1)
                tries += 1

                if self.stop_event.is_set():
                    logger.info("Stop event set, terminating this scrape attempt")
                    return None  # Return None to indicate the process was stopped

            time.sleep(5)
            
            # Check if the "page not found" section is present
            try:
                not_found_element = self.driver.find_element(By.CSS_SELECTOR, '.page-not-found__headline')
                if not_found_element:
                    logger.error("Profile not found or not public")
                    self.stop_event.set()  # Signal other threads to stop
                    return {"error": "Profile not found or not public"}
            except Exception as e:
                logger.info("Profile exists, proceeding with scrape...")

            try:
                logger.info("Attempting to close sign-in popups")
                self.driver.find_element(by=By.CSS_SELECTOR, value='#base-contextual-sign-in-modal > div > section > button').click()
            except Exception:
                try:
                    self.driver.find_element(by=By.CSS_SELECTOR, value='#public_profile_contextual-sign-in > div > section > button').click()
                except Exception:
                    logger.warning("No sign-in popups found")
                    pass
        

            if self.stop_event.is_set():
                logger.info("Stop event set, terminating this scrape attempt")
                return None  # Return None to indicate the process was stopped

            time.sleep(2)
            
            # Extract profile information
            try:
                about = self.driver.find_element(By.CSS_SELECTOR, 'section.core-section-container:nth-child(2) > div:nth-child(2) > p:nth-child(1)').text
            except Exception as e:
                logger.error(f"Could not find About section: {e}")
                about = "Not found"


            if self.stop_event.is_set():
                logger.info("Stop event set, terminating this scrape attempt")
                return None  # Return None to indicate the process was stopped
            
            try:
                headline = self.driver.find_element(by=By.CSS_SELECTOR, value='.top-card-layout__headline').text
            except Exception as e:
                logger.error(f"Could not find headline section: {e}")
                headline = "Not found"


            projectDetailsLi = self.driver.find_elements(by=By.CSS_SELECTOR, value='.personal-project')
            projDetails = '\n'.join([project.text.strip() for project in projectDetailsLi])
            logger.info("Projects found")

            experienceLi = self.driver.find_elements(by=By.CSS_SELECTOR, value='.experience-item')
            experience = '\n'.join([exp.text.strip() for exp in experienceLi])
            logger.info("Experience found")

            certificationLi = self.driver.find_elements(by=By.CSS_SELECTOR, value='.experience-item')
            certificationDetails = '\n'.join([cert.text.strip() for cert in certificationLi])
            logger.info("Certifications found")

            educationDetailsLis = self.driver.find_elements(by=By.CSS_SELECTOR, value='.education__list-item')
            eduDetails = '\n'.join([edu.text.strip() for edu in educationDetailsLis])
            logger.info("Education details found")

            return {
                'about': about,
                'headline': headline,
                'projects': projDetails,
                'experience': experience,
                'certifications': certificationDetails,
                'education': eduDetails,
            }
        
        finally:
            # Ensure resources are cleaned up regardless of how the scrape method exits
            self.cleanup()


@app.route('/', methods=['GET'])
def home():
    logger.info("Home endpoint accessed")
    return (
        "<h1>Hello, World!</h1>"
        "<p>Welcome to the Scraper API!</p>"
        "<p>Use the POST operation on /scrape endpoint with a 'url' query parameter to scrape LinkedIn profile data.</p>"
        "<p>Example: /scrape?url=https://www.linkedin.com/in/some-profile</p>"
        "<p>To use Proxy, send the request as body-> raw-> json { 'url': 'https://www.linkedin.com/in/some-profile', 'proxy': 'http://user:password@proxy-server:port' }</p>"
    )

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        logger.info("Scrape endpoint accessed")
        data = request.json
        url = data.get('url')
        proxy = data.get('proxy')  # Expecting proxy in the request data, e.g., "http://user:password@proxy-server:port"

        if not url:
            logger.error("No URL provided")
            return jsonify({'error': 'URL is required'}), 400

        if proxy:
            if not is_valid_proxy(proxy):
                logger.error("Invalid proxy provided: %s", proxy)
                return jsonify({'error': 'Invalid proxy provided'}), 400
            else:
                logger.info("Using valid proxy: %s", proxy)
        
        # Event to signal that a successful response has been found or profile not found
        stop_event = threading.Event()
        
        # Run the scrape process on two threads: one with login, one without
        with concurrent.futures.ThreadPoolExecutor() as executor:
            scrapper_with_login = Scrapper(proxy=proxy, username=os.getenv('LINKEDIN_USERNAME'), password=os.getenv('LINKEDIN_PASSWORD'), stop_event=stop_event)
            scrapper_without_login = Scrapper(proxy=proxy, stop_event=stop_event)
            
            futures = [
                executor.submit(scrapper_with_login.scrape, url),
                executor.submit(scrapper_without_login.scrape, url)
            ]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    if result and 'error' in result:
                        stop_event.set()  # Signal the other thread to stop if we found a profile not found error
                        logger.info("Profile not found or not public")
                        return jsonify({
                            'status': 'error',
                            'message': result['error']
                        })
                    if result and 'about' in result:
                        stop_event.set()  # Signal the other thread to stop if we have a successful result
                        logger.info("Scraping successful")
                        return jsonify({
                            'status': 'success',
                            'data': result
                        })
                except Exception as e:
                    logger.error("An error occurred during scraping: %s", str(e))
                    continue
        
        logger.error("Linkedin Recaptcha appeared but don't worry you can try again or manually input your details")
        return jsonify({'status': 'error', 'message': "Scrapping Stopped due to recaptcha but don't worry you can try again or manually input your details."}), 500
    
    except ScrapeException as e:
        logger.error("ScrapeException occurred: %s", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
    except Exception as e:
        logger.error("An unexpected error occurred: %s", str(e))
        return jsonify({'status': 'error', 'message': str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 15999))
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port)
