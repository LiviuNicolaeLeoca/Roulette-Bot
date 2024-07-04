import datetime
import math
import re,os
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv

load_dotenv()
superbet_username = os.getenv("SUPERBET_USERNAME")
superbet_password = os.getenv("SUPERBET_PASSWORD")

fibonacci_length=5
bet_amount=0.5
target_dozen="2nd12"

def fibonacci_sequence(length):
    fib = [1, 1]
    while len(fib) < length:
        fib.append(fib[-1] + fib[-2])
    return fib

def extract_last_numbers(page):
    recent_numbers_container = page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator(".recentNumbers--9cf87")

    if recent_numbers_container != None:
        number_containers = recent_numbers_container.locator(".value--877c6").all()
        recent_numbers = [container.inner_text() for container in number_containers]
        return recent_numbers
    else:
        return None

def check_balance(page):
    sold_element = page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator(".balance--46800").inner_text()
    sold_float = re.search(r'\b\d+(?:[.,]\d+)?\b', sold_element)
    sold = float(sold_float.group().replace(',', '.')) if sold_float else "Sold not found"

    return sold


def check_bet(page):
    bet_element = page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator(".totalBet--e866e").inner_text()
    bet_float = re.search(r'\b\d+(?:[.,]\d+)?\b', bet_element)
    bet = float(bet_float.group().replace(',', '.')) if bet_float else "Bet not found"
    return bet


def place_bet_FibonacciDozen(page, fib_sequence, target_dozen):
    dozen = None
    if target_dozen == "1st12":
        dozen = page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator("[data-bet-spot-id='1st12']")
    elif target_dozen == "2nd12":
        dozen = page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator("[data-bet-spot-id='2nd12']")
    elif target_dozen == "3rd12":
        dozen = page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator("[data-bet-spot-id='3rd12']")

    if dozen:
        bet_button = dozen
        try:
            for i in range(fib_sequence):
                page.wait_for_timeout(100)
                bet_button.evaluate('(element) => { \
                const rect = element.getBoundingClientRect(); \
                const offsetX = -15; \
                const offsetY = 0; \
                const clickEvent = new MouseEvent("click", { \
                    bubbles: true, \
                    cancelable: true, \
                    clientX: rect.left + offsetX, \
                    clientY: rect.top + offsetY \
                }); \
                element.dispatchEvent(clickEvent); \
                }')
            
        except Exception as e:
            print(f"Error placing bet: {e}")

def correct_bet(page, desired_bet):
    current_bet = check_bet(page)
    
    if current_bet > desired_bet:
        click_count = math.ceil(desired_bet / current_bet)
        
        for i in range(click_count):
            page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator(".button--9c577").first.click()
        
        bet = check_bet(page)
        if bet == desired_bet:
            print(f"Bet corrected from {current_bet} to {bet}.")
            return bet
        if bet!=desired_bet:
            correct_bet(page, desired_bet)
    else:
        return current_bet

def analyze_bet_outcome(last_numbers, fib_sequence, target_dozen):
    outcome = ""
    if not last_numbers:
        return "unknown"

    last_number = int(last_numbers[0])
    if last_number < 0 or last_number > 36:
        return "unknown"

    if last_number in range(0, 13):
        outcome = "1st12"
    elif last_number in range(12, 25):
        outcome = "2nd12"
    elif last_number in range(24, 37):
        outcome = "3rd12"
    elif last_number == 0:
        outcome = "zero"

    if outcome == target_dozen:
        print(outcome)
        fib_sequence = fibonacci_sequence(fibonacci_length)
        print("Winning!")
    else:
        print(outcome)
        fib_sequence.pop(0)
        print("Losing!")
    return fib_sequence

def place_bet_Fib_Dozen(page,prev_sold,prev_last_numbers,fib_sequence):
    while True:
                sold=0.0
                page.wait_for_timeout(1100)
                current_balance = check_balance(page)
                current_last_numbers = extract_last_numbers(page)
                                
                if current_balance != prev_sold and current_last_numbers[:5] != prev_last_numbers[:5]:
                    page.wait_for_selector("svg",timeout=5*60*1000)
                    page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator("svg").filter(has_text="0,50").locator("circle").nth(1).first.click()

                    print("\n-----------------------------------------------------------------------\n")

                    fib_sequence=analyze_bet_outcome(current_last_numbers,fib_sequence,target_dozen)

                    if len(fib_sequence) == 0:
                        #fib_sequence = fibonacci_sequence(fibonacci_length)
                        print("Out of Fibonacci sequence numbers. Exiting.")
                        break 

                    page.wait_for_timeout(1000)
                    place_bet_FibonacciDozen(page, fib_sequence[0],target_dozen)
                    print(f"Fibonacci sequence: {fib_sequence}")

                    bet=check_bet(page)
                    desired_bet=fib_sequence[0] * bet_amount
                    bet=correct_bet(page, desired_bet)
                    sold = check_balance(page)

                    print("Sold:", sold)
                    print("Bet:", bet)

                    print("Last Numbers:", extract_last_numbers(page))

                    # max=12
                    # if(fibonacci_length<=max):
                    #     if(sold>sum(fib_sequence(fibonacci_length+1))*bet_amount):
                    #         fibonacci_length += 1
                    
                    if sold >= 143.0 or sold == 0 :
                        print("Desired sum acquired or sold balance is lower than 30.5. Exiting.\n")
                        break

                prev_sold = sold
                prev_last_numbers = current_last_numbers

def open_superbet(page):
        page.goto("https://www.google.com/search?q=superbet&oq=superbet&gs_lcrp=EgZjaHJvbWUyBggAEEUYOdIBCDE0MjNqMGoyqAIAsAIB&sourceid=chrome&ie=UTF-8")
        page.get_by_role("button", name="Acceptă tot").click()
        page.get_by_role("link", name="Superbet: Pariuri Sportive").click()
        page.get_by_role("button", name="Accepta").click()
        page.get_by_role("button", name="intră în cont").click()
        page.get_by_role("textbox").first.click()
        page.get_by_role("textbox").first.fill(superbet_username)
        page.locator("input[type=\"password\"]").click()
        page.locator("input[type=\"password\"]").fill(superbet_password)
        page.locator("input[type=\"password\"]").press("Enter")
        page.get_by_role("link", name="casino live").click()
        page.get_by_role("heading", name="Superbet Roulette").click()

        page.frame_locator("#app iframe").frame_locator("iframe[name=\"Gaming Wrapper\"]").frame_locator("iframe").locator("svg").filter(has_text="0,50").locator("circle").nth(1).click()


def run(playwright: Playwright) -> None:
        start_time=datetime.datetime.now()
        print(f"\nRun started at {start_time}.\n")
        fib_sequence = fibonacci_sequence(fibonacci_length)
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        open_superbet(page)

        initial_last_numbers = extract_last_numbers(page)
        prev_last_numbers = initial_last_numbers
        print("Initial Last Numbers:", initial_last_numbers)

        place_bet_FibonacciDozen(page, fib_sequence[0],target_dozen)
        initial_sold = check_balance(page)
        print("Initial Sold:", initial_sold)
        print("Fibonacci Sequence:", fib_sequence)
        initial_bet = check_bet(page)
        desired_bet=fib_sequence[0]*bet_amount
        initial_bet=correct_bet(page, desired_bet)
        print("Initial Bet:", initial_bet)
        prev_sold = initial_sold

        place_bet_Fib_Dozen(page,prev_sold,prev_last_numbers,fib_sequence)

        context.close()
        browser.close()  
        end_time=datetime.datetime.now()
        print(f"\nRun ended at {end_time}.\n")

with sync_playwright() as playwright:
    run(playwright)