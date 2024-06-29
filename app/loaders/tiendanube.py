from app.loaders.utils import BearerAuthApi
from app.loaders.utils import logging
from app.loaders.utils import Dict, List
from datetime import datetime
from app import ROOT_DIR
from app.db.database import DuckDBDatabase
from app.loaders.parsers.parse_orders import parse_orders
from app.loaders.parsers.parse_customers import parse_customers
from app.loaders.parsers.parse_abandoned_checkouts import parse_abandoned_checkouts
from app.loaders.parsers.parse_categories import parse_categories
import pandas as pd
import os


class TiendanubeLoader:
    name = "tiendanube_loader"

    def __init__(self,
                 api_key: str = None,
                 api_host: str = None,
                 load_type: str = None):
        """ Init function to build TiendanubeLoader
        Args:
            api_key: API key for authentication
            api_host: API host URL
            load_type: with the possible following options to load data --> all_customers or all_orders
        Returns:
            Nothing
        """

        # Dates to a "%Y%m%d"
        self.processed_date = str(datetime.now().date().strftime("%Y%m%d"))

        # Api Authorization
        self.api = BearerAuthApi(
            api_key=api_key,
            host=api_host
        )
        self.load_type = load_type
        self.db = DuckDBDatabase(
            db_path=os.path.join(ROOT_DIR, "db/files/folivora_tiendanube", "folivora_tiendanube.duckdb"))

    def load(self):

        if self.load_type == "all_customers":
            logging.info("Executing TiendanubeLoader call for getting All Customers...")

            logging.info(f"Executing api calls...")
            customers = self.get_all_customers()
            logging.info(f"Creating customers_df.")
            customers_df = pd.DataFrame(customers)

            logging.info("Dataframe customers_df Columns:")
            logging.info(customers_df.columns)
            logging.info("Dataframe customers_df Head(5):")
            logging.info(customers_df.head(5))

            # TODO: Remove below lines after testing
            logging.info(f"Dropping database files if exists...")
            self.db.drop_database_file()

            logging.info(f"Saving customers data into database...")
            self.save_into_db(df=customers_df, table_name="customers")
            logging.info(f"Data saved successfully.")

            logging.info(f"Closing connection to database...")
            self.db.disconnect()
            logging.info(f"Connection closed successfully.")

            logging.info(f"TiendanubeLoader call for getting All Customers has been successfully executed!")

        if self.load_type == "all_abandoned_checkouts":
            logging.info("Executing TiendanubeLoader call for getting All Abandoned Carts...")

            logging.info(f"Executing api calls...")
            abandoned_checkouts = self.get_all_abandoned_checkouts()
            logging.info(f"Creating abandoned_checkouts_df.")
            abandoned_checkouts_df = pd.DataFrame(abandoned_checkouts)

            logging.info("Dataframe abandoned_checkouts_df Columns:")
            logging.info(abandoned_checkouts_df.columns)
            logging.info("Dataframe abandoned_checkouts_df Head(5):")
            logging.info(abandoned_checkouts_df.head(5))

            logging.info(f"Connect to the database...")
            con = self.db.connect()

            logging.info(f"Saving abandoned checkouts data into database...")

            logging.info(f"Creating table abandoned_checkouts...")
            logging.info(f"Inserting data into abandoned_checkouts...")
            con.sql(f"CREATE TABLE IF NOT EXISTS abandoned_checkouts AS SELECT * FROM abandoned_checkouts_df")
            con.commit()

            logging.info(f"Data saved successfully.")

            logging.info(f"Closing connection to database...")
            self.db.disconnect()
            logging.info(f"Connection closed successfully.")

            logging.info(f"TiendanubeLoader call for getting All Abandoned Carts has been successfully executed!")

        if self.load_type == "all_categories":
            logging.info("Executing TiendanubeLoader call for getting All Categories...")

            logging.info(f"Executing api calls...")
            categories = self.get_all_categories()
            logging.info(f"Creating categories_df.")
            categories_df = pd.DataFrame(categories)

            logging.info("Dataframe categories_df Columns:")
            logging.info(categories_df.columns)
            logging.info("Dataframe categories_df Head(5):")
            logging.info(categories_df.head(5))

            logging.info(f"Connect to the database...")
            con = self.db.connect()

            logging.info(f"Saving categories data into database...")

            logging.info(f"Creating table categories...")
            logging.info(f"Inserting data into categories...")
            con.sql(f"CREATE TABLE IF NOT EXISTS categories AS SELECT * FROM categories_df")
            con.commit()

            logging.info(f"Data saved successfully.")

            logging.info(f"Closing connection to database...")
            self.db.disconnect()
            logging.info(f"Connection closed successfully.")

            logging.info(f"TiendanubeLoader call for getting All Categories has been successfully executed!")

        if self.load_type == "all_orders":

            logging.info("Executing TiendanubeLoader call for getting All Orders...")

            logging.info(f"Executing api calls...")
            orders = self.get_all_orders()
            logging.info(f"Creating orders_df.")
            orders_df = pd.DataFrame(orders)

            logging.info("Dataframe orders_df Columns:")
            logging.info(orders_df.columns)
            logging.info("Dataframe orders_df Head(5):")
            logging.info(orders_df.head(5))

            # TODO: Remove below lines after testing
            logging.info(f"Dropping database files if exists...")
            self.db.drop_database_file()

            logging.info(f"Connect to the database...")
            con = self.db.connect()

            logging.info(f"Saving customer data into database...")
            # TODO: This doesn't work. Review later!
            # self.save_into_db(df=orders_df, table_name="orders")

            logging.info(f"Creating table orders...")
            logging.info(f"Inserting data into orders...")
            con.sql(f"CREATE TABLE IF NOT EXISTS orders AS SELECT * FROM orders_df")
            con.commit()

            logging.info(f"Data saved successfully.")

            logging.info(f"Closing connection to database...")
            self.db.disconnect()
            logging.info(f"Connection closed successfully.")

            logging.info(f"TiendanubeLoader call for getting All Orders has been successfully executed!")

    def get_request_json_till_last_page(self, endpoint_name: str, page_n: int,
                                        results_per_page: int = 200) -> Dict:
        """ Get Json content for an API Call

        Returns:
            json
        """

        response = self.api.get(
            endpoint=endpoint_name,
            params={
                'per_page': results_per_page,
                'page': page_n,
            },
            extra_headers={"Content-Type": "application/json"}
        )
        if not response.ok:
            logging.info("No-ok response:")
            logging.info(response)
            if response.status_code == 404:
                logging.info(
                    f"All pages have been successfully processed. The last one is reached!"
                )
                response = {}
                return response
            else:
                logging.error(
                    f"There was an error with API endpoint ({response.status_code})."
                )
                logging.error(f"Response:\n {response.text}")
                raise Exception(f"API Error: error code {response.status_code}")

        return response.json()

    def get_all_orders(self) -> List[Dict]:
        """ Get All Orders from Tiendanube API
            Endpoint: GET / orders
            - Api documentation: https://tiendanube.github.io/api-documentation/resources/order#get-orders
            :return: List of orders -> List[Dict]
        """
        orders = []
        # Start from the first page
        page_number = 0

        # TODO: Remove comment from while True
        # while True:
        for i in range(0, 1):
            logging.info(
                f"Processing orders from Page Number: {page_number}"
            )
            r = self.get_request_json_till_last_page(endpoint_name="orders", page_n=page_number)
            # Check if response is empty (including last page case)
            if not r:
                logging.info(
                    f"Reached the last page."
                )
                break

            # Append parsed orders
            orders.extend(parse_orders(r))

            # Increment page number for next iteration
            page_number += 1

        return orders

    def get_all_customers(self) -> List[Dict]:
        """ Get All Customers from Tiendanube API
            Endpoint: GET / customers
            - Api documentation: https://tiendanube.github.io/api-documentation/resources/customer
            :return: List of customers -> List[Dict]
        """
        customers = []
        # Start from the first page
        page_number = 0

        while True:
            logging.info(
                f"Processing customers from Page Number: {page_number}"
            )
            r = self.get_request_json_till_last_page(endpoint_name="customers", page_n=page_number)
            # Check if response is empty (including last page case)
            if not r:
                logging.info(
                    f"Reached the last page."
                )
                break

            # Append parsed customers
            customers.extend(parse_customers(r))

            # Increment page number for next iteration
            page_number += 1

        return customers

    def get_all_abandoned_checkouts(self) -> List[Dict]:
        """ Get All Customers from Tiendanube API
            Endpoint: GET / abandoned-checkout
            - Api documentation: https://tiendanube.github.io/api-documentation/resources/abandoned-checkout
            :return: List of abandoned-checkout -> List[Dict]
        """
        abandoned_checkouts = []
        # Start from the first page
        page_number = 1

        while True:
            logging.info(
                f"Processing abandoned_checkouts from Page Number: {page_number}"
            )
            r = self.get_request_json_till_last_page(endpoint_name="checkouts", page_n=page_number)
            # Check if response is empty (including last page case)
            if not r:
                logging.info(
                    f"Reached the last page."
                )
                break

            # Append parsed abandoned_checkouts
            abandoned_checkouts.extend(parse_abandoned_checkouts(r))

            # Increment page number for next iteration
            page_number += 1

        return abandoned_checkouts

    def get_all_categories(self) -> List[Dict]:
        """ Get All Customers from Tiendanube API
            Endpoint: GET / category
            - Api documentation: https://tiendanube.github.io/api-documentation/resources/category
            :return: List of abandoned-checkout -> List[Dict]
        """
        categories = []
        # Start from the first page
        page_number = 0

        while True:
            logging.info(
                f"Processing categories from Page Number: {page_number}"
            )
            r = self.get_request_json_till_last_page(endpoint_name="categories", page_n=page_number)
            # Check if response is empty (including last page case)
            if not r:
                logging.info(
                    f"Reached the last page."
                )
                break

            # Append parsed categories
            categories.extend(parse_categories(r))

            # Increment page number for next iteration
            page_number += 1

        return categories

    # TODO: This does not work. Review later!
    def save_into_db(self, df: pd.DataFrame, table_name: str):
        """
        Create tables in the database
        :return: None
        """

        # Connect to the database
        con = self.db.connect()

        logging.info(f"Creating table {table_name}...")
        logging.info(f"Inserting data into {table_name}...")
        con.sql(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM {df}")

        con.commit()
