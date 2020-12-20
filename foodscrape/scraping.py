from bs4 import BeautifulSoup
from urllib.request import urlopen

def makesoup(url):
    """ This function takes a url and make a BeautifulSoup object from it
    returns soup object
    """
    with urlopen(url) as page:
        html = page.read().decode("utf-8")
        return BeautifulSoup(html,"html.parser")

def convertedstr(string):
    """ This function takes a string containing non-ascii numerals and converts said numerals within the string
    returns string
    """
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
        '\u215e':'7/8',
        '\u0026':'&'
    }

    for ch in string:
        if ch in unwanted.keys():
            out.append(unwanted[ch])
        else:
            out.append(ch)
    return "".join(out);

def prepopulate_links(linklist,visited):
    """This function takes in the visited list and linklist and appends every link stored in
    links.txt the program has encountered in previous runs to these
    """
    with open('links.txt','r') as f:
        for line in f:
            linklist.append(str(line).strip())
            visited.add(str(line).strip())
        f.close()

def save_link(link):
    with open('links.txt','a') as f:
        f.write('{}\n'.format(link))
        f.close()

class AllRecipeBook:
    """ Data store for url links to allrecipes.com recipes

    This class leverages Beautiful Soup to scrape allrecipes.com, extracting a master list of recipe urls for later processing

    Attributes:
    visited     -- set; holds the names of subcategories that have been processed
    linklist    -- list; holds the urls of recipes that have been processed

    Methods:
    __init__    -- initializes the recipebook's data fields and calls the makebook method
    findall     -- returns a list of urls of either carousel recipe types or card recipes
    makebook    -- this function recurses down recipe type tree to extract all urls and append them to link file
    """
    def __init__(self,url):
        self.linklist = []
        self.visited = set()
        self.makebook(url)

    def findall(self,soup):
        """ This function returns the next set of subcategories or recipes
        returns a tuple holding names of subcategories/recipes and the associated list of urls

        Parameter:
        :soup: BeautifulSoup object holding url html
        """
        try:
            carousel = soup.body.main.find_all("a",class_="carouselNav__link recipeCarousel__link")
            if carousel:
                carousel_names = soup.body.main.find_all("div",class_="carouselNav__linkText")
                return carousel_names,carousel
        except:
            print('Attempted to access empty carousel')
            print(soup.name)
            return -1,-1
        try:
            card = soup.body.main.find_all("a",class_="card__titleLink manual-link-behavior")
            return None,card
        except:
            print('Attempeted to access bad recipe card')
            print(soup.name)
            return -1,-1

    def makebook(self,url):
        """ This function creates the master list of links to all recipes recursively
        This method creates a soup object for the current url, extracts subcategories/recipes,
        and for each returned list value, either recursively calls itself or appends to master list

        Parameter:
        :url: string holding url link to webpage of next subcategory or recipe
        """
        # prepopulate visited list with links from previous runs to speed up initial computation
        prepopulate_links(self.linklist,self.visited)
        # if url is in linklist, then skip completely
        if url in self.linklist:
            return
        # create soup for current url page
        soup = makesoup(url)
        soup.name = url
        # figure out whether there are subcategories and get list, otherwise, get list of recipes
        names,lst = self.findall(soup)
        # if returns -1, then skip completely
        if names == -1:
            return
        # if subcategories exist, iterate through all and process each
        if names is not None:
            for name,sub in zip(names,lst):
                n = str(name.string).strip()
                if n not in self.visited:
                    self.visited.add(n)
                    self.makebook(sub.get("href"))
        # if no more subcategories, gather all recipe links
        else:
            for recipe in lst:
                link = recipe.get("href")
                if link not in self.linklist:
                    self.linklist.append(link)
                    save_link(link)


    
    def getname(self):
        """ This function fetches the name of the recipe
        returns a string containing the name of the current recipe
        """
        name = soup.body.main.find("h1",class_='headline heading-content')
        return name.string.strip()

    def getstars(self):
        """ This function fetches the average 5-star rating of the recipe
        returns a string with the average 5-star rating
        """
        stars = self.soup.body.find("span",class_='review-star-text')
        return float(stars.string.strip())

    def getstuff(self):
        """ This function fetches the listed ingredients of the recipe
        returns a set containing the listed ingredients
        """
        out = set()
        for ing in self.soup.body.main.find_all("span",class_='ingredients-item-name'):
            s = ing.string.strip()
            if not s.isascii():
                s = convertedstr(s)
            out.add(s)
        return out

    def getnutri(self):
        """ This function fetches the nutrition facts of the recipe
        returns a dictionary of key:value pairs containing nutrition info
        """
        out = {}
        
        names = self.soup.body.find_all("span",class_='nutrient-name')
        vals = self.soup.body.find_all("span",class_='nutrient-value')

        for name,val in zip(names,vals):
            out[name.contents[0].strip()] = [val.contents[0].strip()]

        return out

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

def scrape_links():
    # create the master list of recipes
    url = "https://www.allrecipes.com/recipes/"
    book = AllRecipeBook(url).linklist

if __name__ == "__main__":
    scrape_links()