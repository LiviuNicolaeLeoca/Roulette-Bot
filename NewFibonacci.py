import datetime
import math
import re
import os
from playwright.sync_api import Playwright, sync_playwright, expect
from dotenv import load_dotenv

load_dotenv()
superbet_username = os.getenv("SUPERBET_USERNAME")
superbet_password = os.getenv("SUPERBET_PASSWORD")

fibonacci_length = 6
bet_amount = 0.5
reset_count=1
target_dozen=""

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

    frame_locator = page.frame_locator("#app iframe").frame_locator("iframe")
    frame_locator.locator('[data-role="statistics-button"]').first.click()

    frame_locator.locator('[data-label="ULTIMELE 500"]').first.click()

    page.frame_locator("#app iframe").frame_locator("iframe").locator("svg").filter(has_text="0,50").locator("circle").nth(1).first.click()

def fibonacci_sequence(length):
    fib = [1, 1]
    while len(fib) < length:
        fib.append(fib[-1] + fib[-2])
    return fib

def extract_last_numbers(page):
    recent_numbers_container = page.frame_locator("#app iframe").frame_locator("iframe").locator(".recentNumbers--9cf87")
    

    if recent_numbers_container:
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

def place_bet_FibonacciDozen(page, fib_sequence, target_dozen):
    dozen_locator = page.frame_locator("#app iframe").frame_locator("iframe").locator(f"[data-bet-spot-id='{target_dozen}']")
    if dozen_locator:
        bet_button = dozen_locator
        try:
            for _ in range(fib_sequence):
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
        for _ in range(click_count):
            page.frame_locator("#app iframe").frame_locator("iframe").locator(".button--9c577").first.click()
        bet = check_bet(page)
        if bet == desired_bet:
            print(f"Bet corrected from {current_bet} to {bet}.")
            return bet
        if bet != desired_bet:
            correct_bet(page, desired_bet)
    else:
        return current_bet

def analyze_bet_outcome(last_numbers, fib_sequence, target_dozen,page):
    outcome = ""
    if not last_numbers:
        return "unknown", fib_sequence, target_dozen
    last_number = int(last_numbers[0])
    if last_number < 0 or last_number > 36:
        print("Last number not found!")
        return fib_sequence, target_dozen
    if 1<=last_number <=12:
        outcome = "1st12"
    elif 13<=last_number <=24:
        outcome = "2nd12"
    elif 25<=last_number <=36:
        outcome = "3rd12"
    elif last_number == 0:
        outcome = "zero"
    if outcome == target_dozen:
        print(outcome)
        fib_sequence = fibonacci_sequence(fibonacci_length)
        target_dozen = find_last_dozen(last_numbers,page)
        print("Win!")
    else:
        print(outcome)
        fib_sequence.pop(0)
        print("Loss!")
    return fib_sequence, target_dozen

def place_bet_Fib_Dozen(page, prev_sold, prev_last_numbers, fib_sequence, target_dozen):
    reset_count=0
    while True:
        sold = 0.0
        page.wait_for_timeout(1000)
        current_balance = check_balance(page)
        current_last_numbers = extract_last_numbers(page)
        current_dozen=target_dozen
        if current_balance != prev_sold and current_last_numbers[:6] != prev_last_numbers[:6]:
            try:
                page.wait_for_selector("svg")
                page.frame_locator("#app iframe").frame_locator("iframe").locator("svg").filter(has_text="0,50").locator("circle").nth(1).first.click()
            except TimeoutError:
                print("TimeoutError")
            
            print("\n-----------------------------------------------------------------------\n")
            fib_sequence, target_dozen = analyze_bet_outcome(current_last_numbers, fib_sequence, current_dozen, page)

            if len(fib_sequence) == 0:
                if(reset_count>2):
                    break
                page.wait_for_timeout(10*60*1000)
                print("Out of Fibonacci sequence numbers.")
                reset_count+=1
                break
    
            page.wait_for_timeout(1000)
            place_bet_FibonacciDozen(page, fib_sequence[0], target_dozen)
            print(f"Fibonacci sequence: {fib_sequence}")

            bet = check_bet(page)
            desired_bet = fib_sequence[0] * bet_amount
            bet = correct_bet(page, desired_bet)
         
            print("Bet placed on:", target_dozen)
            print("Bet:", bet)
            sold = check_balance(page)
            print("Sold:", sold)
            print("Last Numbers:", extract_last_numbers(page))
            print(calculate_dozen_frequency(getLast100Numbers(page)))
            if sold >= 300.0 or sold < 0.5:
                print("Desired sum acquired or sold balance is 0. Exiting.\n")
                break
        prev_sold = sold
        prev_last_numbers = current_last_numbers

def find_last_dozen(last_numbers, page):
    last_numbers = [int(num) for num in last_numbers]  
    dozen_order = []
    dozens={}
    last_hunnid=getLast100Numbers(page)
    dozens=calculate_dozen_frequency(last_hunnid)
    if(len(last_hunnid)>51):
        return None
    threshold=0.3*len(last_hunnid)
    
    eligible_dozens = [dozen for dozen, count in dozens.items() if count >= threshold]
    dozen_counts = {dozen: 0 for dozen in eligible_dozens}
    for number in last_numbers:
        if 1 <= number <= 12 and "1st12" in dozen_counts:
            dozen_counts["1st12"] += 1
        elif 13 <= number <= 24 and "2nd12" in dozen_counts:
            dozen_counts["2nd12"] += 1
        elif 25 <= number <= 36 and "3rd12" in dozen_counts:
            dozen_counts["3rd12"] += 1
        
        dozen_order.append("1st12" if 1 <= number <= 12 else ("2nd12" if 13 <= number <= 24 else ("3rd12" if 25 <= number <= 36 else None)))
        
        if all(count > 0 for count in dozen_counts.values()):
            for dozen in reversed(dozen_order):
                if dozen in eligible_dozens:
                    return dozen.strip()

    return None

def getLast100Numbers(page):
    frame_locator = page.frame_locator("#app iframe").frame_locator("iframe")
    number_elements_locator = frame_locator.locator('.contentElement--e8ecb > .numbers--2435c > div > .single-number--43778 > .value--877c6')
    
    # Extract numbers from the current frame if last numbers are not available
    page.frame_locator("#app iframe").frame_locator("iframe").locator('.contentElement--e8ecb > .numbers--2435c > div > .single-number--43778 > .value--877c6').first.wait_for()
    numbers = extract_last_numbers(page)+[element.text_content() for element in number_elements_locator.all()]

    return numbers[13:]

def calculate_dozen_frequency(numbers):
    dozens_frequency = {"1st12": 0, "2nd12": 0, "3rd12": 0}
    for number in numbers:
        number = int(number)
        if 1 <= number <= 12:
            dozens_frequency["1st12"] += 1
        elif 13 <= number <= 24:
            dozens_frequency["2nd12"] += 1
        elif 25 <= number <= 36:
            dozens_frequency["3rd12"] += 1
    return dozens_frequency

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
    print("Fibonacci Sequence:", fib_sequence)
    target_dozen=find_last_dozen(initial_last_numbers,page)
    place_bet_FibonacciDozen(page, fib_sequence[0],target_dozen)
    print("Bet on:",target_dozen)
    initial_bet = check_bet(page)
    print("Initial Bet:", initial_bet)
    initial_sold = check_balance(page)
    prev_sold = initial_sold
    print("Initial Sold:", initial_sold)
    print(calculate_dozen_frequency(getLast100Numbers(page)))

    place_bet_Fib_Dozen(page,prev_sold,prev_last_numbers,fib_sequence,target_dozen)

    context.close()
    browser.close()  
    end_time=datetime.datetime.now()
    print(f"\nRun ended at {end_time}.\n")

with sync_playwright() as playwright:
    run(playwright)

