import csv
import os
import math
from OrderProcessor import *

class DispatchProcessor:

    def __init__(self,driver):
        self.driver = driver

    def get_all_csv_files_in_folder(self,folder_path):
        csv_files = []

        for filename in os.listdir(folder_path):
            if filename.endswith('.csv'):
                file_path = os.path.join(folder_path, filename)
                csv_files.append(file_path)

        return csv_files

    def get_all_column_values(self,file_path):
        rows_data = []

        with open(file_path, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if 'Order number' in row[0]:
                    continue
                rows_data.append(row[0])

        return rows_data

    def get_dispath_info_from_csv(self,file_path):
        driver = self.driver
        dispathc_id = file_path.split('#')[1].split('-')[0]
        driver.get(f"https://ops.miswag.co/dispatches/{dispathc_id}")
        try:
            xpath = '/html/body/div[2]/div[1]/main/div/section/header[1]/div[1]/h1'

            dispatch_header = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.XPATH, xpath))
            )

            get_dispatch_date = dispatch_header.text.strip().split(' - ')[1].split(' ')[0]

            order_date_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", get_dispatch_date)
            if order_date_match:
                order_date = order_date_match.group(0).replace("-", "/")
                return datetime.strptime(order_date, "%d/%m/%Y").replace(hour=0, minute=0, second=0)
            else:
                print(f"Error: No date found in text: {get_dispatch_date}")
                return None

        except Exception as e:
            print(f"Error extracting order date: {e}")
            return None

    def get_dispatch_info(self):
        driver = self.driver
        header_xpath = '/html/body/div[2]/div[1]/main/div/section/header[1]/div[1]/h1'

        dispatch_header = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, header_xpath))
        )

        dispatch_match = re.search(r"#(\d+)", dispatch_header.text.strip())
        get_dispatch_id = dispatch_match.group(1) if dispatch_match else None

        get_dispatch_date = dispatch_header.text.strip().split(' - ')[1].split(' ')[0]

        get_dispatch_match = re.search(r"(\d{2})/(\d{2})/(\d{4})", get_dispatch_date)
        dispatch_date = get_dispatch_match.group(0).replace("-", "/")

        orders_count_xpath = '/html/body/div[2]/div[1]/main/div/section/header[2]/div/div/div[1]/span'
        dispatch_orders_count = int(WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, orders_count_xpath))
        ).text.strip())
        agent_xpath = '/html/body/div[2]/div[1]/main/div/section/header[2]/div/div/div[2]/span'
        dispatch_agent = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, agent_xpath))
        ).text.strip()
        dispatcher_xpath = '/html/body/div[2]/div[1]/main/div/section/header[2]/div/div/div[3]/span'
        dispatcher = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, dispatcher_xpath))
        ).text.strip()

        pages = math.ceil(dispatch_orders_count / 100)

        result = {page: min(100, dispatch_orders_count - (page - 1) * 100) for page in range(1, pages + 1)}
        return {
            'id': get_dispatch_id,
            'agent': dispatch_agent,
            'dispatcher': dispatcher,
            'date': dispatch_date,
            'orders_count': dispatch_orders_count,
            'pages': result
        }

    def get_order_links(self):
        driver = self.driver
        order_links = []
        missing_count = 0  # Counter to track consecutive missing rows

        for row in range(2, 102):  # Loop from row 2 to 101
            order_link_xpath = f'//*[@id="relationManager0"]/div/div/div/div[2]/table/tbody/tr[{row}]/td[10]/div/div/a'

            try:
                order_link = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, order_link_xpath))
                ).get_attribute('href')
                order_links.append(order_link)
                missing_count = 0  # reset the counter if an order is found
            except:
                missing_count += 1  # increment counter for a missing row

                if missing_count >= 2:
                    break
        return order_links

        # return order_links

    def set_per_page_to_max(self):
        driver = self.driver
        per_page = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable(
                (By.XPATH, '//*[@id="relationManager0"]/div/div/div/nav/div/label[2]/div/div[2]/select/option[4]')
            )
        )
        per_page.click()
