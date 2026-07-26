# Importing necessary libraries
import tkinter as tk  # GUI library for creating the interface
from tkinter import messagebox  # For showing error or info messages in the GUI
import requests  # For making HTTP requests to eBay
from bs4 import BeautifulSoup  # For parsing the HTML response from eBay
import pandas as pd  # For handling and saving scraped data in DataFrames
import plotly.express as px  # For generating interactive graphs

# eBay Scraper Function: Fetches data from eBay for a search term and page number
def get_data(searchterm, page=1):
    # Construct the eBay search URL for the given search term and page number
    URL = f"https://www.ebay.com/sch/i.html?_nkw={searchterm}&_sacat=0&_from=R40&LH_PrefLoc=3&LH_Auction=1&rt=nc&LH_Sold=1&LH_Complete=1&_pgn={page}"
    try:
        # Make a request to the URL and wait for the response
        r = requests.get(URL, timeout=10)
        r.raise_for_status()  # If request fails, this raises an exception
        soup = BeautifulSoup(r.text, "html.parser")  # Parse the HTML content of the page
        return soup
    except requests.RequestException as e:
        # Show error message if the connection fails
        messagebox.showerror("Error", f"Connection failed: {e}")
        return None

# Function to extract product data from the parsed HTML (soup)
def parse(soup):
    if soup is None:
        return []  # Return an empty list if no data is fetched
    productslist = []  # This will store all the product details
    # Find all the product listing elements on the page
    results = soup.find_all('li', {'class': 's-item'})
    for item in results:
        try:
            # Extract title, price, bids, and link of each product
            title = item.find("div", {"class": "s-item__title"}).text
            price = item.find("span", {"class": "s-item__price"}).text
            sold_date = item.find("span", {"class": "s-item__caption--signal POSITIVE"}).text
            bids = item.find("span", {"class": "s-item__bids"}).text
            link = item.find("a", {"class": "s-item__link"})["href"]
            product = {
                "Title": title,
                "Sold_Price": float(price.replace("$", "").replace(",", "").strip()),
                "Sold_Date": sold_date,
                "Bids": bids,
                "Link": link
            }
            productslist.append(product)  # Add the product data to the list
        except:
            continue  # If any data extraction fails, skip to the next item
    return productslist

# Function to save the data to CSV and Excel files, and return the data as a pandas DataFrame
def output(productslist, searchterm):
    if not productslist:
        return None  # Return None if no data was collected
    productsdf = pd.DataFrame(productslist)  # Create a DataFrame from the product list
    # Save the DataFrame to CSV and Excel files
    productsdf.to_csv(f"{searchterm}_output.csv", index=False)
    productsdf.to_excel(f"{searchterm}_output.xlsx", index=False)
    return productsdf  # Return the DataFrame for further use

# Tkinter GUI Class: This defines the user interface and logic for the application
class eBayScraperGUI:
    def __init__(self, root):
        self.root = root  # The root Tkinter window
        self.root.title("eBay Scraper")  # Window title
        self.root.geometry("600x400")  # Window size

        # Add input fields for search term and number of pages
        tk.Label(root, text="Search Term:").grid(row=0, column=0, padx=10, pady=10)
        self.search_entry = tk.Entry(root, width=30)
        self.search_entry.insert(0, "iPhone")  # Default search term
        self.search_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(root, text="Number of Pages:").grid(row=1, column=0, padx=10, pady=10)
        self.pages_entry = tk.Entry(root, width=10)
        self.pages_entry.insert(0, "3")  # Default number of pages to scrape
        self.pages_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Start scraping button
        self.scrape_button = tk.Button(root, text="Start Scraping", command=self.start_scraping)
        self.scrape_button.grid(row=2, column=0, columnspan=2, pady=10)

        # Button to show the Plotly graph (disabled until scraping is done)
        self.plotly_button = tk.Button(root, text="Show Plotly Graph", command=self.show_plotly_graph, state="disabled")
        self.plotly_button.grid(row=5, column=0, columnspan=2, pady=10)

        # Status label to show current status to the user
        self.status_label = tk.Label(root, text="Status: Ready", fg="blue")
        self.status_label.grid(row=6, column=0, columnspan=2, pady=10)

        self.df = None  # This will hold the DataFrame of scraped data

    def start_scraping(self):
        searchterm = self.search_entry.get().strip()  # Get search term from input field
        try:
            max_pages = int(self.pages_entry.get())  # Get number of pages to scrape
            if max_pages <= 0:
                raise ValueError("Number of pages must be greater than 0")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of pages")
            return

        self.status_label.config(text="Status: Scraping...", fg="orange")  # Update status
        self.scrape_button.config(state="disabled")  # Disable the scrape button
        self.root.update()

        all_products = []  # List to store all scraped products
        for page in range(1, max_pages + 1):
            self.status_label.config(text=f"Status: Scraping page {page}...")  # Show current page being scraped
            self.root.update()
            soup = get_data(searchterm, page)  # Fetch data for current page
            if soup is None:
                break
            current_products = parse(soup)  # Parse the data to get product info
            if not current_products:
                self.status_label.config(text="Status: No more results", fg="red")
                break
            all_products.extend(current_products)  # Add the products to the list

        self.df = output(all_products, searchterm)  # Save data and get DataFrame
        if self.df is not None:
            self.status_label.config(text="Status: Saved successfully", fg="green")  # Success
            self.plotly_button.config(state="normal")  # Enable the Plotly graph button
        else:
            self.status_label.config(text="Status: No data to save", fg="red")  # If no data found
        self.scrape_button.config(state="normal")  # Re-enable the scrape button

    def show_plotly_graph(self):
        if self.df is None or self.df.empty:
            messagebox.showerror("Error", "No data available for plotting")
            return

        try:
            # Prepare data for Plotly graph
            df_plot = self.df.copy()
            df_plot["Short_Title"] = df_plot["Title"].str[:20]  # Shorten the title for graph display
            df_plot["Bids"] = df_plot["Bids"].str.extract(r"(\d+)").astype(float)  # Extract bid count and convert to float

            # Drop rows with NaNs in the Bids column
            df_plot.dropna(subset=["Bids"], inplace=True)

            # Create the Plotly bar chart
            fig = px.bar(
                df_plot,
                x="Short_Title",  # Use shortened title for x-axis
                y="Bids",  # Number of bids for y-axis
                title="Interactive Product Bids",
                labels={"Short_Title": "Product", "Bids": "Number of Bids"},
                hover_data=["Title", "Sold_Price", "Sold_Date", "Link"]  # Hover information
            )
            fig.update_layout(xaxis_tickangle=-45)  # Rotate the x-axis labels for better readability
            fig.show()  # Show the graph in the browser

        except Exception as e:
            messagebox.showerror("Plotly Error", f"Failed to generate Plotly chart:\n{e}")  # Error handling for Plotly

# Main part of the code: running the application
if __name__ == "__main__":
    root = tk.Tk()  # Create the main window
    app = eBayScraperGUI(root)  # Create an instance of the scraper GUI class
    root.mainloop()  # Start the Tkinter main event loop