from bs4 import BeautifulSoup
from urllib.request import urlopen

def makesoup(url):
    """ This function makes a soup object

    This function takes a url and returns a BeautifulSoup object from it containing webpage html
    :url: str; contains webpage
    """
    with urlopen(url) as page:
        html = page.read().decode("utf-8")
        return BeautifulSoup(html,"html.parser")

def convertedstr(string):
    """ This function cleans a string

    This function takes a string containing non-ascii numerals and converts said numerals within the string
    :string: str; holds string that might contain non-ASCII characters
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

def prepopulate_links(linklist,num=0,stop=None,visited=set()):
    """ If "links.txt" exists, prepopulates master lists to avoid unnecessary complications
    
    This function takes in the visited list and linklist and appends every link stored in
    "links.txt"
    :linklist: list; master list of all recipe urls to be filled
    :num: int; holds starting line number
    :stop: int; holds the ending line number, None by default
    :visited: set; running list of visited recipe subcategory names
    """
    with open('links.txt','r') as f:
        for i in range(num):
            f, next()
        for i,line in enumerate(f):
            if stop not None:
                if i >= stop:
                    f.close()
                    return
            linklist.append(str(line).strip())
            visited.add(str(line).strip())
        f.close()

def save_link(link):
    """ This function handles writing of data to "links.txt"

    The function writes recipe url to the file "links.txt"
    :link: str; contains recipe url
    """
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
            carousel = soup.body.find_all("a",class_="carouselNav__link recipeCarousel__link")
            if carousel:
                carousel_names = soup.body.find_all("div",class_="carouselNav__linkText")
                return carousel_names,carousel
        except:
            print('Attempted to access empty carousel')
            print(soup.name)
            return -1,-1
        try:
            card = soup.body.find_all("a",class_="card__titleLink manual-link-behavior")
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
        # if url is gallery type, then skip completely
        if url.find("https://www.allrecipes.com/gallery/") != -1:
            return
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
    geterr     -- returns a boolean indicating if any scraping error occured
    """
    def __init__(self,url):
        self.soup = makesoup(url)
        self.name = self.getname()
        self.rating = self.getstars()
        self.ingredients = self.getstuff()
        self.nutrition = self.getnutri()
        self.err = self.geterr()
    
    def getname(self):
        """ This function fetches the name of the recipe
        returns a string containing the name of the current recipe
        """
        # attempt to scrape recipe title, otherwise return None
        try:
            name = self.soup.find("h1",class_='headline heading-content')
        except:
            return None
        if name:
            return name.string.strip()
        else:
            return None

    def getstars(self):
        """ This function fetches the average 5-star rating of the recipe
        returns a string with the average 5-star rating
        """
        # extract average ratings value if possible, otherwise return None
        try:
            stars = self.soup.body.find(attrs={"data-ratings-average":True})['data-ratings-average']
        except:
            return None
        return float(stars) if stars != '' else None

    def getstuff(self):
        """ This function fetches the listed ingredients of the recipe
        returns a set containing the listed ingredients
        """
        # initialize output set of ingredients and scrape list of them if possible
        out = set()
        try:
            ings = self.soup.body.find_all("span",class_='ingredients-item-name')
        except:
            return None
        # if empty, return None
        if not ings:
            return None
        # iterate over all ingredients and parse them in case of hyperlinks, adding to set
        for ing in ings:
            if len(ing.contents)>1:
                s = ""
                for i in ing.contents:
                        s += "{} ".format(i.string.strip())
            else:
                s = ing.string.strip()
            # if any string contains non-ascii characters, replace them
            if not s.isascii():
                s = convertedstr(s)
            out.add(s)
        return out

    def getnutri(self):
        """ This function fetches the nutrition facts of the recipe
        returns a dictionary of key:value pairs containing nutrition info
        """
        # initialize output dictionary and initiliaze name:value pairs if possible
        out = {}
        try:
            names = self.soup.body.find_all("span",class_='nutrient-name')
            vals = self.soup.body.find_all("span",class_='nutrient-value')
        except:
            return None
        # if no error, standardize names, record the pairs in dictionary and return
        standardize(names,vals)
        for name,val in zip(names,vals):
            out[name.contents[0].strip()[:-1]] = [val.contents[0].strip()]
        return sorted(out)

    def geterr(self):
        if self.name is None or self.nutrition is None or self.rating is None or self.ingredients is None:
            return True
        return False

def standardize(names,vals):
    """ This function regularizes nutrition names

    This function ensures that nutrition names adhere such that overlapping features are not created
    :names: list; holds all names of nutrition items
    :vals: list; holds all associated values to names
    """
    # create standardization set
    standard = {
        "fat":"Total Fat",
        "saturated fat":"Saturated Fat",
        "cholesterol":"Cholesterol",
        "sodium":"Sodium",
        "potassium":"Potassium",
        "carbohydrates":"Total Carbohydrates",
        "dietary fiber":"Dietary Fiber",
        "protein":"Protein",
        "sugars":"Sugars",
        "vitamin a iu":"Vitamin A",
        "vitamin c":"Vitamin C",
        "calcium":"Calcium",
        "iron":"Iron",
        "thiamin":"Thiamin",
        "niacin equivilants":"Niacin",
        "vitamin b6":"Vitamin B6",
        "magnesium":"Magnesium",
        "folate":"Folate"
    }
    # more easily compact names
    names = [name.contents[0].strip()[:-1] for name in names]
    # for items already in names, make sure it is standardized value
    for i,name in enumerate(names):
        if standard.get(name.lower()):
            names[i] = standard.get(name.lower())
    # for items not in names, add
    for notin in set(standard.keys()).difference(names):
        names.append(standard.get(notin))
        vals.append('-')

def scrape_links():
    """ Create the master list of recipes
    
    This function creates an AllRecipeBook instance for allrecipes.com/recipes and extracts the created linklist
    """
    url = "https://www.allrecipes.com/recipes/"
    book = AllRecipeBook(url).linklist

if __name__ == "__main__":
    scrape_links()