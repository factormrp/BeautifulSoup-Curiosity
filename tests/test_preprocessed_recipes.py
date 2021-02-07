import requests
from foodscrape.scraping import Recipe
from foodscrape.scraping import scrape_links

def main():
    book = scrape_links(20)
    for url in book:
        r = Recipe(url,True)

if __name__ == "__main__":
    main()