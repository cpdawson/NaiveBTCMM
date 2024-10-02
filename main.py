from coinbase.rest import RESTClient
from json import dumps
from decimal import Decimal
import time
import os
import csv
import threading
import time


# Function to generate the next client order ID
def get_next_order_id():
    CSV_FILE = 'order_ids.csv'
    last_order_id = "00000000"

    # Check if the file exists
    if os.path.exists(CSV_FILE):
        # Read the last order ID from the file
        with open(CSV_FILE, mode='r', newline='') as file:
            reader = csv.reader(file)
            rows = list(reader)
            if rows:
                last_order_id = rows[-1][0]

    # Increment the order ID
    next_order_id = str(int(last_order_id) + 1).zfill(8)

    # Write the new order ID to the file
    with open(CSV_FILE, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([next_order_id])

    return next_order_id


# Replace these with your actual API key and secret
api_key = "organizations/43208e8e-70f3-4171-a9ee-dd4e0b02fbe4/apiKeys/29ba2d6b-4b6b-4a71-b6b4-46b05b80afee"
api_secret = "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIGqr2Jkzc8a7tVe4oq5olpDd1GDHrKwwR4qJXvfTXtbhoAoGCCqGSM49\nAwEHoUQDQgAEg+IfOAj7kHc96fqVDbe/wR/xMQuBAJG79C1JKksh+o9C/pr7arHT\nWRaiIqQbGUGSLA/FHy1Vn01B95MaF+K94g==\n-----END EC PRIVATE KEY-----\n"

client = RESTClient(api_key=api_key, api_secret=api_secret)

product_id = "ROSE-USD"
usd_size = "0.00004405"

while True:
    def calculate_spread(data):
        bid = float(data['pricebooks'][0]['bids'][0]['price'])
        ask = float(data['pricebooks'][0]['asks'][0]['price'])
        return ask - bid


    spread = calculate_spread(client.get_best_bid_ask(product_id))
    spread_percentage = spread / float(client.get_product(product_id)['price']) * 100
    print(f"Spread: {spread} USD ({spread_percentage}%)")
    time.sleep(1)  # pause for 1 second




def place_and_cancel_orders():
    while True:
        product = client.get_best_bid_ask("BTC-USD")
        bid = float(product['pricebooks'][0]['bids'][0]['price'])
        ask = float(product['pricebooks'][0]['asks'][0]['price'])
        spread_size = ask - bid
        if spread_size > 3:
            limit_bid_price = "{:.2f}".format(bid + (spread_size / 8))
            limit_ask_price = "{:.2f}".format(ask - (spread_size / 8))

            # Generate unique order IDs
            limit_bid_order_id = get_next_order_id()
            limit_ask_order_id = get_next_order_id()

            # Place bid and ask orders in parallel
            def place_order(order_type, client_order_id, limit_price):
                if order_type == 'buy':
                    order = client.limit_order_gtc_buy(
                        client_order_id=client_order_id,
                        product_id=product_id,
                        base_size=usd_size,
                        limit_price=limit_price)
                    print(f"Bought at: {limit_price}")
                else:
                    order = client.limit_order_gtc_sell(
                        client_order_id=client_order_id,
                        product_id=product_id,
                        base_size=usd_size,
                        limit_price=limit_price)
                    print(f"Sold at: {limit_price}")
                return order

            bid_thread = threading.Thread(target=place_order, args=('buy', limit_bid_order_id, limit_bid_price))
            ask_thread = threading.Thread(target=place_order, args=('sell', limit_ask_order_id, limit_ask_price))

            bid_thread.start()
            ask_thread.start()

            bid_thread.join()
            ask_thread.join()

            # Wait and then cancel orders in parallel
            def cancel_order(order_id):
                client.cancel_orders(order_ids=[order_id])

            time.sleep(1)
            cancel_bid_thread = threading.Thread(target=cancel_order, args=(limit_bid_order_id,))
            cancel_ask_thread = threading.Thread(target=cancel_order, args=(limit_ask_order_id,))

            cancel_bid_thread.start()
            cancel_ask_thread.start()

            cancel_bid_thread.join()
            cancel_ask_thread.join()

            break

        time.sleep(0.1)


# Start the threaded order placement and cancellation
threading.Thread(target=place_and_cancel_orders).start()
