import random
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright, Page, BrowserContext, Locator
from playwright_stealth import Stealth
from utils.pw_helper import get_random_delay, handle_cookies_request, perform_action, take_screenshot
from constants.output import OUTPUT_FOLDER, LOG_FILENAME
from pw_context import get_new_context
from scrapper_config import CONFIG
from logger import translation_logger


logger = translation_logger.get_logger(
    output_folder=OUTPUT_FOLDER,
    log_filename=LOG_FILENAME
)

url = "https://wplace.live/"

def puppeter_browser(
    batch_msg: str,
    headless: bool = True):
    
    with Stealth().use_sync(sync_playwright()) as p:
        browser, context = get_new_context(playwright=p, headless=headless, msg_prefix=batch_msg)
        page = context.new_page()
        
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            window.chrome = { runtime: {}, app: {}, LoadTimes: function(){} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)        
        
     
        # logger.info(f"{batch_msg} {len(batch)} sentences")
        perform_action(lambda: page.goto(url, timeout=CONFIG["page_timeout_ms"]), f"{batch_msg} goto")
        # handle_cookies_request(page=page, batch_msg=batch_msg)
        
   
        logger.debug(f"{batch_msg} Filtering logs.")
        batch_msg = batch_msg.split('|')[0]

        get_random_delay([30, 60])                           
        translation_logger.filter_log(
            filter_func=lambda line: batch_msg in line,
            new_filename=batch_msg,
            output_folder="filtered_logs",
            msg=batch_msg
        )
              
        context.close()
        browser.close()

        return True

puppeter_browser("test 1", False)