import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from DispatchProcessor import *

def manage_cookies(driver, cookies_file):
    if os.path.exists(cookies_file):
        with open(cookies_file, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print("Cookies loaded successfully.")
    else:
        input("Please log in manually and press Enter to save cookies...")
        with open(cookies_file, "wb") as f:
            pickle.dump(driver.get_cookies(), f)
        print("Cookies saved successfully.")

def get_urls_from_file(file_path):
    url_pattern = re.compile(r'^(https?://[^\s]+)$')

    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.read().splitlines()

    urls = [line.strip() for line in lines if url_pattern.match(line.strip())]
    return urls


def save_results_to_file(dispatch_date, dispatch_id, perfect_orders, imperfect_orders):
    folder_name = f"results/{dispatch_date.replace('/', '-')}"

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    perfect_file_path = os.path.join(folder_name, f"{dispatch_id}-perfect.txt")
    with open(perfect_file_path, 'w', encoding='utf-8') as perfect_file:
        perfect_file.write(f"Perfeect Orders : {len(perfect_orders)}\n\n")
        for order in perfect_orders:
            perfect_file.write(order['order_number']+"\n")
            # perfect_file.write(f"Results: {order['results']}\n")
            # perfect_file.write("=" * 50 + "\n")

    imperfect_file_path = os.path.join(folder_name, f"{dispatch_id}-imperfect.txt")
    with open(imperfect_file_path, 'w', encoding='utf-8') as imperfect_file:
        imperfect_file.write(f"Imperfeect Orders : {len(imperfect_orders)}\n\n")
        for order in imperfect_orders:
            imperfect_file.write(order['order_number']+"\n")
            # imperfect_file.write(f"Results: {order['results']}\n")
            # imperfect_file.write("=" * 50 + "\n")

    print(f"Results saved for dispatch {dispatch_id}.")

def main():
    options = Options()
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-infobars")
    driver = webdriver.Chrome(options=options)

    cookies_file = "cookies.pkl"
    try:
        driver.get("https://ops.miswag.co/login")
        manage_cookies(driver, cookies_file)
        driver.refresh()

        dispatch_processor = DispatchProcessor(driver)
        dispatches = get_urls_from_file('urls.txt')
        if len(dispatches) >= 1:
            for dispatch_url in dispatches:
                driver.get(dispatch_url)
                dispatch_info = dispatch_processor.get_dispatch_info()
                print(dispatch_info)

                all_orders = []
                perfect_orders = []
                imperfect_orders = []

                dispatch_date = dispatch_info['date']
                dispatch_id = dispatch_info['id']

                for page, orders_count in dispatch_info['pages'].items():
                    page_prefix = f"{dispatch_url}?page={page}"
                    driver.get(page_prefix)
                    dispatch_processor.set_per_page_to_max()
                    links = dispatch_processor.get_order_links()
                    all_orders.extend(links)

                print("Collected Orders:", len(all_orders))
                order_processor = OrderProcessor(driver)

                for order in all_orders:
                    driver.get(order)
                    order_date = order_processor.get_order_date()
                    order_comments = order_processor.get_order_comments()
                    order_number = order_processor.get_oder_number()
                    clean_comments = order_processor.clean_comments_list(order_comments)
                    order_dispatches = order_processor.get_order_dispatches(comments=order_comments)
                    is_perfect = order_processor.is_perfect(order_date, clean_comments, order_dispatches)

                    if is_perfect['status'] == 'perfect':
                        perfect_orders.append({'status': 'perfect', 'order': order , 'order_number': order_number, 'results': is_perfect})
                    else:
                        imperfect_orders.append({'status': 'imperfect', 'order': order , 'order_number': order_number, 'results': is_perfect})

                save_results_to_file(dispatch_date, dispatch_id, perfect_orders, imperfect_orders)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
