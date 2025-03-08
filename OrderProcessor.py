import json
from datetime import datetime, timedelta
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class OrderProcessor:
    def __init__(self, driver):
        self.driver = driver

    def calculate_valid_days(self, order_date, dispatch_date):
        with open('settings.json', 'r', encoding='utf-8') as file:
            settings = json.load(file)

        off_days = settings.get("off_days", [])
        if isinstance(dispatch_date, str):
            dispatch_date = datetime.strptime(dispatch_date, "%Y-%m-%d %H:%M:%S")

        # Handle cases where off_days is None, empty, or missing
        if not off_days:
            off_days = []
        else:
            off_days = [datetime.strptime(day, "%d/%m/%Y") for day in off_days]

        valid_days = 0
        current_date = order_date

        while current_date <= dispatch_date:
            # Skip Fridays (weekday() == 4) and off days
            if current_date not in off_days and current_date.weekday() != 4:
                valid_days += 1
            current_date += timedelta(days=1)

        return valid_days

    def get_order_date(self):
        try:
            driver = self.driver
            xpath = '/html/body/div[2]/div[1]/main/div/section/header/div[1]/div[2]/div[2]'

            order_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )

            get_order_date = order_element.text.strip()

            order_date_match = re.search(r"(\d{2})-(\d{2})-(\d{4})", get_order_date)
            if order_date_match:
                order_date = order_date_match.group(0).replace("-", "/")
                return datetime.strptime(order_date, "%d/%m/%Y").replace(hour=0, minute=0, second=0)
            else:
                # print(f"Error: No date found in text: {get_order_date}")
                return None

        except Exception as e:
            # print(f"Error extracting order date: {e}")
            return None

    def get_oder_number(self):
        driver = self.driver
        xpath = '/html/body/div[2]/div[1]/main/div/section/header/div[1]/div[2]/div[1]/h1'
        order_number = driver.find_element(By.XPATH,xpath).text.split()[0]
        return order_number

    def get_order_comments(self):
        driver = self.driver

        # Wait for the comments to be present in the DOM
        try:
            comments = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "space-y-5 border-b")]'))
            )


            comments_list = []  # List to hold the comment data

            for comment_div in comments:
                try:
                    # Extract comment text, commentor, and comment date
                    comment_text = comment_div.find_element(By.XPATH,
                                                            './/div[contains(@class, "my-3 font-semibold")]').text.strip()
                    commentor = comment_div.find_element(By.XPATH,
                                                         './/div[contains(@class, "bg-blue-400")]/span').text.strip()
                    comment_date = comment_div.find_element(By.XPATH,
                                                            './/div[contains(@class, "ml-4 bg-blue-400")]/span').text.strip()

                    comments_list.append({
                        'commentor': commentor,
                        'date': comment_date,
                        'comment': comment_text
                    })


                except Exception as e:
                    # print(f"Error processing comment: {e}")
                    continue

            return comments_list

        except Exception as e:
            # print(f"Error waiting for comments: {e}")
            return []

    def get_order_dispatches(self, comments):
        dispatches = {}

        for idx, comment in enumerate(comments):
            if "تم تسليم الطلبية للتوصيل" in comment['comment'].lower():
                dispatches[idx] = comment['date']

        return dispatches

    def clean_comments_list(self, comments):
        last_dispatch = comments[max(self.get_order_dispatches(comments))]

        last_dispatch_index = next((index for index, comment in enumerate(comments) if comment == last_dispatch), -1)

        cleaned_comments = comments[:last_dispatch_index + 1] if last_dispatch_index != -1 else comments

        return cleaned_comments

    def is_valid_apple_serial(self,serial):
        standard_pattern = r'^[A-Z0-9]{10,12}$'  # Standard Apple serials (10-12 chars)
        extended_pattern = r'^[A-Z0-9]{15,22}$'  # Longer serials (e.g., SCC2HC000XMA0000556)

        return bool(re.fullmatch(standard_pattern, serial)) or bool(re.fullmatch(extended_pattern, serial))

    def check_comments_list(self, un_cleared_comments, settings_file='settings.json'):
        comments = self.clean_comments_list(un_cleared_comments)

        with open(settings_file, 'r', encoding='utf-8') as file:
            settings = json.load(file)

        allowed_comments = settings.get("allowed_comments", [])
        allowed_keywords = settings.get("allowed_keywords", [])

        for comment in comments:
            comment_text = comment['comment']

            # If comment is in allowed comments, continue
            if comment_text in allowed_comments:
                continue

            # Check if comment contains an allowed keyword
            if any(keyword in comment_text for keyword in allowed_keywords):
                continue

            # Check if comment is or contains an Apple serial number
            words = re.findall(r'[A-Z0-9]+', comment_text)  # Extract alphanumeric words
            if any(self.is_valid_apple_serial(word) for word in words):
                continue

            return False

        return True

    def is_perfect(self, order_date, comments, order_dispatches):

        # Step 1: Check for disallowed comments
        if self.check_comments_list(comments) == False:
            return {
                'status': 'imperfect',
                'reason': 'comments',
                'msg': "The order has comments which are not allowed.",
                'comments': comments
            }

        # Step 2: Validate order_dispatches
        if not order_dispatches or not all(isinstance(i, int) for i in order_dispatches):
            return {
                'status': 'imperfect',
                'reason': 'invalid dispatch data',
                'msg': "Invalid dispatch data provided.",
                'order_dispatches': order_dispatches
            }

        # Step 3: Get the latest dispatch date
        try:
            latest_dispatch_index = max(order_dispatches)
            order_dispatch_date = comments[latest_dispatch_index]['date']
        except (IndexError, KeyError, TypeError) as e:
            return {
                'status': 'imperfect',
                'reason': 'dispatch retrieval error',
                'msg': f"Error retrieving dispatch date: {e}",
                'order_dispatches': order_dispatches
            }

        # Step 4: Convert dates to datetime format
        try:
            order_date = datetime.strptime(order_date, '%Y-%m-%d %H:%M:%S') if isinstance(order_date,
                                                                                          str) else order_date
            dispatch_datetime = datetime.strptime(order_dispatch_date, '%Y-%m-%d %H:%M:%S')
        except ValueError as e:
            return {
                'status': 'imperfect',
                'reason': 'date format error',
                'msg': f"Invalid date format: {e}",
                'order_date': order_date,
                'dispatch_datetime': order_dispatch_date
            }

        # Step 5: Calculate valid business days
        validate_date = self.calculate_valid_days(order_date, dispatch_datetime)

        # Step 6: Check allowed period
        if validate_date > 3:
            return {
                'status': 'imperfect',
                'reason': 'passed allowed period',
                'msg': 'Order Passed Allowed Period (3 days)',
                'validate_date': validate_date
            }

        return {'status': 'perfect'}
