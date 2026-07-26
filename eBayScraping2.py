import tkinter as tk
from tkinter import messagebox, ttk
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import plotly.express as px
import io
import time

# eBay Scraping Functions
def get_data(searchterm, page=1):
    URL = f"https://www.ebay.com/sch/i.html?_nkw={searchterm}&_sacat=0&_from=R40&LH_PrefLoc=3&LH_Auction=1&rt=nc&LH_Sold=1&LH_Complete=1&_pgn={page}"
    try:
        r = requests.get(URL, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        return soup
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Connection failed: {e}")
        return None

def parse(soup):
    if soup is None:
        return []
    productslist = []
    results = soup.find_all('li', {'class': 's-item'})
    for item in results:
        try:
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
            productslist.append(product)
        except:
            continue
    return productslist

def output(productslist, searchterm):
    if not productslist:
        return None
    productsdf = pd.DataFrame(productslist)
    productsdf.to_csv(f"{searchterm}_output.csv", index=False)
    productsdf.to_excel(f"{searchterm}_output.xlsx", index=False)
    return productsdf

# Tkinter GUI with Plotly Integration
class eBayScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("eBay Scraper")
        self.root.geometry("800x600")

        # Input fields
        tk.Label(root, text="Search Term:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.search_entry = tk.Entry(root, width=40)
        self.search_entry.insert(0, "iPhone")
        self.search_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(root, text="Number of Pages:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.pages_entry = tk.Entry(root, width=10)
        self.pages_entry.insert(0, "3")
        self.pages_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Buttons
        self.scrape_button = tk.Button(root, text="Start Scraping", command=self.start_scraping)
        self.scrape_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.plotly_button = tk.Button(root, text="Show Plotly Graph", command=self.show_plotly_graph, state="disabled")
        self.plotly_button.grid(row=3, column=0, columnspan=2, pady=10)

        # Status label
        self.status_label = tk.Label(root, text="Status: Ready", fg="blue")
        self.status_label.grid(row=4, column=0, columnspan=2, pady=10)

        # Table for results
        self.tree = ttk.Treeview(root, columns=("Title", "Sold_Price", "Sold_Date", "Bids", "Link"), show="headings")
        self.tree.heading("Title", text="Title")
        self.tree.heading("Sold_Price", text="Sold Price ($)")
        self.tree.heading("Sold_Date", text="Sold Date")
        self.tree.heading("Bids", text="Bids")
        self.tree.heading("Link", text="Link")
        self.tree.column("Title", width=200)
        self.tree.column("Sold_Price", width=100)
        self.tree.column("Sold_Date", width=100)
        self.tree.column("Bids", width=100)
        self.tree.column("Link", width=200)
        self.tree.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Scrollbar
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=5, column=2, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Configure grid
        root.grid_rowconfigure(5, weight=1)
        root.grid_columnconfigure(1, weight=1)

        self.df = None
        self.plot_frame = None

    def start_scraping(self):
        searchterm = self.search_entry.get().strip()
        try:
            max_pages = int(self.pages_entry.get())
            if max_pages <= 0:
                raise ValueError("Number of pages must be greater than 0")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of pages")
            return

        # Clear previous table data
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.status_label.config(text="Status: Scraping...", fg="orange")
        self.scrape_button.config(state="disabled")
        self.plotly_button.config(state="disabled")
        self.root.update()

        all_products = []
        for page in range(1, max_pages + 1):
            self.status_label.config(text=f"Status: Scraping page {page}...")
            self.root.update()
            soup = get_data(searchterm, page)
            if soup is None:
                break
            current_products = parse(soup)
            if not current_products:
                self.status_label.config(text="Status: No more results", fg="red")
                break
            all_products.extend(current_products)
            time.sleep(1)  # Avoid rate limiting

        self.df = output(all_products, searchterm)
        if self.df is not None:
            self.status_label.config(text="Status: Saved successfully", fg="green")
            self.plotly_button.config(state="normal")
            # Populate table
            for _, row in self.df.iterrows():
                self.tree.insert("", "end", values=(
                    row["Title"][:50],  # Truncate for display
                    f"{row['Sold_Price']:.2f}",
                    row["Sold_Date"],
                    row["Bids"],
                    row["Link"][:50]
                ))
        else:
            self.status_label.config(text="Status: No data to save", fg="red")
        self.scrape_button.config(state="normal")

    def show_plotly_graph(self):
        if self.df is None or self.df.empty:
            messagebox.showerror("Error", "No data available for plotting")
            return

        try:
            # Prepare data for Plotly
            df_plot = self.df.copy()
            df_plot["Short_Title"] = df_plot["Title"].str[:20]
            df_plot["Bids"] = df_plot["Bids"].str.extract(r"(\d+)").astype(float)
            df_plot.dropna(subset=["Bids"], inplace=True)

            # Create Plotly figure
            fig = px.bar(
                df_plot,
                x="Short_Title",
                y="Bids",
                title="Interactive Product Bids",
                labels={"Short_Title": "Product", "Bids": "Number of Bids"},
                hover_data=["Title", "Sold_Price", "Sold_Date", "Link"]
            )
            fig.update_layout(xaxis_tickangle=-45)

            # Convert Plotly figure to image and display in Tkinter
            img_buf = io.BytesIO()
            fig.write_image(img_buf, format="png")
            img_buf.seek(0)

            # Clear previous plot frame if it exists
            if self.plot_frame:
                self.plot_frame.destroy()

            # Create new frame for the plot
            self.plot_frame = tk.Toplevel(self.root)
            self.plot_frame.title("Plotly Graph")
            self.plot_frame.geometry("800x600")

            # Load and display the image
            from PIL import Image, ImageTk
            img = Image.open(img_buf)
            photo = ImageTk.PhotoImage(img)
            canvas = tk.Label(self.plot_frame, image=photo)
            canvas.image = photo  # Keep a reference
            canvas.pack()

        except Exception as e:
            messagebox.showerror("Plotly Error", f"Failed to generate Plotly chart:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = eBayScraperGUI(root)
    root.mainloop()