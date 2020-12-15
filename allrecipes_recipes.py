import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen

""" This function takes a url and make a BeautifulSoup object from it
returns soup object
"""
def makesoup(url):
    with urlopen(url) as page:
        html = page.read().decode("utf-8")
        return BeautifulSoup(html,"html.parser")

""" This function takes a string containing non-ascii numerals and converts said numerals within the string
returns string
"""
def convertedstr(string):
    out = []
    unwanted = {
        '\u2009':' ',
        '\u00bc':'1/4',
        '\u00bd':'1/2',
        '\u00be':'3/4',
        '\u2153':'1/3',
        '\u2154':'2/3',
        '\u2155':'1/5',
        '\u2156':'2/5',
        '\u2157':'3/5',
        '\u2158':'4/5',
        '\u2159':'1/6',
        '\u215a':'5/6',
        '\u215b':'1/8',
        '\u215c':'3/8',
        '\u215d':'5/8',
        '\u215e':'7/8'
    }

    for ch in string:
        if ch in unwanted.keys():
            out.append(unwanted[ch])
        else:
            out.append(ch)
    return "".join(out);


class AllRecipeBook:
""" Data store for url links to allrecipes.com recipes

This class leverages Beautiful Soup to scrape allrecipes.com, extracting a master list of recipe urls for later processing

Attributes:
carousel    -- str; holds html class reference for carousel of recipe type links
card        -- str; holds html class reference for card of recipe link
linklist    -- list; holds all of the urls to each recipe
count       -- int; holds number of times traversed down recipe type tree

Methods:
__init__    -- initializes the recipebook's data fields and calls the makebook method
findall     -- returns a list of urls of either carousel recipe types or card recipes
makebook    -- this function recurses down recipe type tree to extract all urls and append them to linklist
"""
    def __init__(self,url):
        self.carousel = "carouselNav__link recipeCarousel__link"
        self.card = "card__titleLink manual-link-behavior"
        self.linklist = []
        self.count = 0
        self.makebook(url)

    # this function returns the next set of subcategories
    # returns a tuple holding boolean if carousel and associated list of urls
    def findall(self,soup):
        crl = soup.body.main.find_all("a",self.carousel)
        crd = soup.body.main.find_all("a",self.card)
        return (1,crl) if crl != [] else (0,crd) 

    # this function creates the master list of links to all recipes recursively
    def makebook(self,url):
        # create soup for current url page
        soup = makesoup(url)
        # figure out whether there are subcategories and get list, otherwise, get list of recipes
        tipe,lst = self.findall(soup)
        # if subcategories exist, iterate through all and process each
        if(tipe and self.count < 5):
            for sub in lst:
                self.count += 1
                self.makebook(sub.get("href"))
        # if no more subcategories, gather all recipe links
        else:
            for recipe in lst:
                self.linklist.append(recipe.get("href"))
            self.count = 0


class Recipe:
""" Data store for important features of a recipe

This class leverages Beautiful soup to scrape a recipe webpage, extracting useful features for later processing

Attributes:
soup    -- BeautifulSoup; holds the object reference to the page html
name    -- str; holds the title of the recipe
rating  -- float; holds the average rating of the recipe
ingredients -- set; holds all of the listed ingredients of recipe as well as their quantities
nutrition   -- dict; holds nutrition name:value pairs

Methods:
getname    -- returns a string holding title of the recipe
getstars   -- returns a float holding average 5-star rating
getstuff   -- returns a set of ingredients listed in the recipe along with their quantities
getnutri   -- returns a dict of nutrition name:value pairs 
"""
    def __init__(self,url):
        self.soup = makesoup(url)
        self.name = self.getname()
        self.rating = self.getstars()
        self.ingredients = self.getstuff()
        self.nutrition = self.getnutri()

    # This function fetches the name of the recipe
    # returns a string
    def getname(self):
        name = self.soup.body.main.find("h1",class_='headline heading-content')
        return name.string.strip()

    # This function fetches the average 5-star rating of the recipe
    # returns a string
    def getstars(self):
        stars = self.soup.body.find("span",class_='review-star-text')
        return float(stars.string.strip())

    # this function fetches the listed ingredients of the recipe
    # returns a set
    def getstuff(self):
        out = set()
        for ing in self.soup.body.main.find_all("span",class_='ingredients-item-name'):
            s = ing.string.strip()
            if not s.isascii():
                s = convertedstr(s)
            out.add(s)
        return out

    # this function fetches the nutrition facts of the recipe
    # returns a dictionary of key:value pairs
    def getnutri(self):
        out = {}
        
        names = self.soup.body.find_all("span",class_='nutrient-name')
        vals = self.soup.body.find_all("span",class_='nutrient-value')

        for name,val in zip(names,vals):
            out[name.contents[0].strip()] = val.contents[0].strip()

        return out

def main():
    url = "https://www.allrecipes.com/recipes/"
    book = RecipeBook(url)

    names = []
    ratings = []
    

    #writer = pd.ExcelWriter('recipes.xlsx',engine='xlsxwriter')
    #df.to_excel(writer,sheet_name='Sheet1',index=False)
    #writer.save()

    #for link in book.linklist:
    #    r = Recipe(link)



if __name__ == "__main__":
    main()