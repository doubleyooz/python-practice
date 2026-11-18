import random
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright, Page, BrowserContext, Locator
from playwright_stealth import Stealth
from utils.pw_helper import get_random_delay, handle_cookies_request, perform_action, take_screenshot
from constants.output import OUTPUT_FOLDER, LOG_FILENAME
from constants.game_hook import GAME_HOOK
from pw_context import get_new_context
from scrapper_config import CONFIG
from logger import translation_logger
from solver_2048 import best_move
from lzstring import LZString

logger = translation_logger.get_logger(
    output_folder=OUTPUT_FOLDER,
    log_filename=LOG_FILENAME
)

url = "https://play2048.co/"

def get_board_state(page, batch_msg):
    board = page.evaluate("() => window.__board")
    if board is None:
        logger.warning(f"{batch_msg} __board still null")
    return board
    
def puppeter_browser(
    batch_msg: str,
    headless: bool = True):
    
    with Stealth().use_sync(sync_playwright()) as p:
        browser, context = get_new_context(
            playwright=p,
            headless=headless, 
            smaller_screens=True, 
            msg_prefix=batch_msg
        )
        page = context.new_page()
        
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false});
            window.chrome = { runtime: {}, app: {}, LoadTimes: function(){} };
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)  
        page.add_init_script(GAME_HOOK)
  
        # logger.info(f"{batch_msg} {len(batch)} sentences")
                  
        page.on("pageerror", lambda err: logger.error(f"PAGE ERROR: {err}"))
        perform_action(lambda: page.goto(url, timeout=CONFIG["page_timeout_ms"]), f"{batch_msg} goto")
        # handle_cookies_request(page=page, batch_msg=batch_msg)
    
        
        logger.debug(f"{batch_msg} Filtering logs.")
        batch_msg = batch_msg.split('|')[0]

        get_random_delay([0.3, 0.6])                           
        
        
        text = get_board_state(page, batch_msg)
        logger.warning(f"{batch_msg} text: {text}")

        page.wait_for_selector("canvas", timeout=15000)
        get_random_delay([1, 4])        
        for fr in page.frames:
            try:
                info = fr.evaluate("""() => ({
                    url: location.href,
                    canvases: document.querySelectorAll('canvas').length,
                    tileMap: !!window.__tileMap,
                    installed: !!window.__tileHookInstalled,
                    setCount: window.__setCount ?? null,
                })""")
                logger.info(f"{batch_msg} FRAME {fr.url} -> {info}")
            except Exception as e:
                logger.info(f"{batch_msg} FRAME {fr.url} -> ERROR {e}")
        # page.locator("button.bg-near-black.absolute.right-0.top-0").click()
        final_board = play_2048(
            page=page,
            logger=logger,
            batch_msg=batch_msg,
            max_moves=5000,
            move_delay_ms=0.1
        ) 
        logger.info(f"{batch_msg} final_board {final_board}")
        translation_logger.filter_log(
            filter_func=lambda line: batch_msg in line,
            new_filename=batch_msg,
            output_folder="filtered_logs",
            msg=batch_msg
        )
        context.close()
        browser.close()

        return True
    

def play_2048(page, logger, batch_msg, max_moves: int = 5000, move_delay_ms: float = 0.6):
    page.bring_to_front()
    page.wait_for_timeout(400)

    try:
        page.locator("canvas").first.click(timeout=3000)
    except Exception as e:
        logger.warning(f"{batch_msg} canvas click failed: {e}")

    # Prime: press a few keys so the game populates its tile Map
    for i in range(6):
        page.keyboard.press(["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"][i % 4])
        page.wait_for_timeout(400)

    maps = page.evaluate("() => window.__dumpMaps ? window.__dumpMaps() : []")
    logger.info(f"{batch_msg} setCount={page.evaluate('() => window.__setCount')}")
    logger.info(f"{batch_msg} MAPS DUMP:")
    for m in maps:
        logger.info(f"{batch_msg}   {m}")

    board = get_board_state(page, batch_msg)
    logger.info(f"{batch_msg} board after priming: {board}")

    # If reader still failed, dump a couple of actual tile values from each Map
    if not any(any(row) for row in board):
        for i in range(min(len(maps), 10)):
            details = page.evaluate(f"""() => {{
                const m = window.__mapList[{i}];
                if (!m) return null;
                const out = [];
                let n = 0;
                for (const [k, v] of m) {{
                    out.push({{ k: String(k).slice(0, 30),
                               vType: typeof v,
                               vKeys: v && typeof v === 'object' ? Object.keys(v) : null,
                               vValue: v && typeof v === 'object' ? v.value : v }});
                    if (++n >= 3) break;
                }}
                return out;
            }}""")
            logger.info(f"{batch_msg} MAP[{i}] entries: {details}")
   
    take_screenshot(page, f"{batch_msg}_primed.png", msg_prefix=batch_msg)
    button = page.get_by_role("button", name="Keep Going")
    for move_num in range(max_moves):    
        if button.is_visible():
            button.click()
        board = get_board_state(page, batch_msg)
        if not any(any(row) for row in board):
            page.keyboard.press("ArrowLeft")
            get_random_delay(2, 5)
            board = get_board_state(page, batch_msg)
        if not any(any(row) for row in board):
            logger.warning(f"{batch_msg} empty at move {move_num}, "
                           f"setCount={page.evaluate('() => window.__setCount')}")
            break
        direction, best_score = best_move(board, 2, logger)
        logger.info(f"{batch_msg} move: {move_num}, direction: {direction}, score: {best_score:.2f}")
        if direction is None:
            logger.info(f"{batch_msg} game over at move {move_num}, max: {max(max(r) for r in board)}")
            break
        page.keyboard.press(f"Arrow{direction.capitalize()}")
        get_random_delay([move_delay_ms, move_delay_ms * 1.3])
        if move_num % 50 == 0:
            logger.info(f"{batch_msg} move {move_num} max: {max(max(r) for r in board)}")

    take_screenshot(page, f"{batch_msg}_final_board.png", msg_prefix=batch_msg)
    return get_board_state(page, batch_msg)

puppeter_browser("test 1", False)