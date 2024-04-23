import datetime
import math
import re,os
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv

load_dotenv()
superbet_username = os.getenv("SUPERBET_USERNAME")
superbet_password = os.getenv("SUPERBET_PASSWORD")

fibonacci_length = 6
bet_amount=0.5
def fibonacci_sequence(length):
    fib = [1, 1]
    while len(fib) < length:
        fib.append(fib[-1] + fib[-2])
    return fib


def extract_last_numbers(page):
    recent_numbers_container = page.frame_locator("#app iframe").frame_locator("iframe").locator(".recentNumbers--9cf87")

    if recent_numbers_container != None:
        number_containers = recent_numbers_container.locator(".value--877c6").all()
        recent_numbers = [container.inner_text() for container in number_containers]
        return recent_numbers
    else:
        return None

def check_balance(page):
    sold_element = page.frame_locator("#app iframe").frame_locator("iframe").locator(".balance--46800").inner_text()
    sold_float = re.search(r'\b\d+(?:[.,]\d+)?\b', sold_element)
    sold = float(sold_float.group().replace(',', '.')) if sold_float else "Sold not found"

    return sold


def check_bet(page):
    bet_element = page.frame_locator("#app iframe").frame_locator("iframe").locator(".totalBet--e866e").inner_text()
    bet_float = re.search(r'\b\d+(?:[.,]\d+)?\b', bet_element)
    bet = float(bet_float.group().replace(',', '.')) if bet_float else "Bet not found"
    return bet


def place_bet_FibonacciDozen(page, fib_sequence):
    bet_button = page.frame_locator("#app iframe").frame_locator("iframe").locator("[data-bet-spot-id='3rd12']")
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
    
    if current_bet != desired_bet:
        click_count = math.ceil(desired_bet / current_bet)
        
        for i in range(click_count):
            page.frame_locator("#app iframe").frame_locator("iframe").locator(".button--9c577").first.click()
        
        bet = check_bet(page)
        #page.frame_locator("#app iframe").frame_locator("iframe").get_by_text("ANULARE").click()
        if bet == desired_bet:
            print(f"Bet corrected from {current_bet} to {bet}.")
            return bet
        if bet!=desired_bet:
            correct_bet(page, desired_bet)
    else:
        return current_bet

def place_bet_Fib_Dozen(page,prev_sold,prev_last_numbers,fib_sequence):
    while True:
                sold=0.0
                page.wait_for_timeout(1100)
                current_balance = check_balance(page)
                current_last_numbers = extract_last_numbers(page)
                                
                if current_balance != prev_sold and current_last_numbers[:5] != prev_last_numbers[:5]:
                    page.wait_for_selector("svg",timeout=5*60*1000)
                    page.frame_locator("#app iframe").frame_locator("iframe").locator("svg").filter(has_text="0,50").locator("circle").nth(1).first.click()

                    sold = check_balance(page)

                    print("\n-----------------------------------------------------------------------\n")
                
                    page.wait_for_timeout(1000)
                    last_number = int(extract_last_numbers(page)[0])
                    if last_number or last_number == 0:
                        last_number = int(extract_last_numbers(page)[0])
                        if last_number < 25 or last_number > 36:
                            print(f"Last number is {last_number}, indicating a losing bet.")
                            fib_sequence.pop(0)
                                
                        elif 25 <= last_number <= 36:
                            fib_sequence = fibonacci_sequence(fibonacci_length)
                            print(f"Last number is {last_number}, indicating a winning bet. Resetting sequence.")
                            
                    elif last_number == None:
                        print("No last numbers found.")
                        if sold<prev_sold:
                            print("Sold balance is less than previous sold balance.")
                            fib_sequence.pop(0)
                        elif sold > prev_sold:
                            print("Sold balance is higher than previous sold balance. Resetting sequence.")
                            fib_sequence = fibonacci_sequence(fibonacci_length)
                    else:
                        print("Nothing found!!!!")
                        break

                    if len(fib_sequence) == 0:
                        #fib_sequence = fibonacci_sequence(fibonacci_length)
                        print("Out of Fibonacci sequence numbers. Exiting.")
                        break 

                    place_bet_FibonacciDozen(page, fib_sequence[0])
                    print(f"Fibonacci sequence: {fib_sequence}")
                    
                    print("Sold:", sold)
                    bet=check_bet(page)
                    desired_bet=fib_sequence[0] * bet_amount
                    bet=correct_bet(page, desired_bet)

                    print("Bet:", bet)
                    last_numbers=extract_last_numbers(page)
                    last_number = int(last_numbers[0])
                    print("Last Numbers:", extract_last_numbers(page))

                    if sold >= 71.5 or sold == 0 :
                        print("Desired sum acquired or sold balance is lower than 30.5. Exiting.\n")
                        break

                prev_sold = sold
                prev_last_numbers = current_last_numbers


def run(playwright: Playwright) -> None:

    log_file_path = "console_logs.txt"
    with open(log_file_path, "w") as log_file:
        start_time=datetime.datetime.now()
        log_file.write(f"\nRun started at {start_time}.\n")
        fib_sequence = fibonacci_sequence(fibonacci_length)
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
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

        page.wait_for_selector("svg",timeout=60*1000)
        page.frame_locator("#app iframe").frame_locator("iframe").locator("svg").filter(has_text="0,50").locator("circle").nth(1).first.click()

        initial_last_numbers = extract_last_numbers(page)
        prev_last_numbers = initial_last_numbers
        print("Initial Last Numbers:", initial_last_numbers)
        log_file.write("Initial Last Numbers: " + str(initial_last_numbers) + "\n")
        initial_sold = check_balance(page)
        print("Initial Sold:", initial_sold)
        log_file.write("Initial Sold: " + str(initial_sold) + "\n")
        print("Fibonacci Sequence:", fib_sequence)
        log_file.write("Fibonacci Sequence: " + str(fib_sequence) + "\n")
        place_bet_FibonacciDozen(page, fib_sequence[0])

        initial_bet = check_bet(page)
        desired_bet=fib_sequence[0]*bet_amount
        initial_bet=correct_bet(page, desired_bet)
        print("Initial Bet:", initial_bet)
        log_file.write("Initial Bet: " + str(initial_bet) + "\n")
        prev_sold = initial_sold

        place_bet_Fib_Dozen(page,prev_sold,prev_last_numbers,fib_sequence)

        context.close()
        browser.close()  
        end_time=datetime.datetime.now()
        log_file.write(f"\nRun ended at {end_time}.\n")

with sync_playwright() as playwright:
    run(playwright)