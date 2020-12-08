"""
This program runs the section with iterates over the carousel of recipe types
to extract types as separate recipe groups
"""

import re
from bs4 import BeautifulSoup
from urllib.request import urlopen

def makesoup(url):
    page = urlopen(url)
    html = page.read().decode("utf-8")
    return BeautifulSoup(html,"html.parser")

# this function takes a string containing non-ascii numerals and converts said numerals within the string
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

"""
This wrapper class leverages Beautiful Soup to scrape allrecipes.com,
extracting a master list of recipe urls for later processing
"""
class RecipeBook:

    def __init__(self,url):
        self.carousel = "carouselNav__link recipeCarousel__link"
        self.card = "card__titleLink manual-link-behavior"
        self.linklist = []
        self.count = 0
        self.makebook(url)

    # this function returns the next set of subcategories
    def findall(self,soup):
        crl = soup.body.main.find_all("a",self.carousel)
        crd = soup.body.main.find_all("a",self.card)
        return (1,crl) if crl != [] else (0,crd) 

    # this function creates the master list of links to all recipes
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

"""
This class is a data store for important features
"""
class Recipe:

    ratedata = "component recipe-reviews"
    name = "headline heading-content"
    summ = "margin-0-auto"
    item = "ingredients-item-name"

    def __init__(self,url):
        self.soup = makesoup(url)
        self.name = self.getname()
        self.rating = self.getstars()
        self.ingredients = self.getstuff()
        self.nutrition = self.getnutri()

    def getname(self):
        name = self.soup.body.main.find("h1",class_='headline heading-content')
        return name.string.strip()

    def getstars(self):
        stars = self.soup.body.find("span",class_='review-star-text')
        return stars.string.strip()

    def getstuff(self):
        out = []
        for ing in self.soup.body.main.find_all("span",class_='ingredients-item-name'):
            s = ing.string.strip()
            if not s.isascii():
                s = convertedstr(s)
            out.append(s)
        return out

    def getnutri(self):
        out = {}
        
        names = self.soup.body.find_all("span",class_='nutrient-name')
        vals = self.soup.body.find_all("span",class_='nutrient-value')

        for name,val in zip(names,vals):
            out[name.contents[0].strip()] = val.contents[0].strip()

        return out

def main():
    url = "https://www.allrecipes.com/recipes/"
    url2 = "https://www.allrecipes.com/recipe/17855/glazed-corned-beef/"

    book = RecipeBook(url)

if __name__ == "__main__":
    main()