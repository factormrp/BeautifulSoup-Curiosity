import requests
from re import search
from bs4 import BeautifulSoup
from textblob import TextBlob as tb

# GLOBAL request session store to reuse connections
r_sesh = requests.Session()

# GLOBAL constant for default scraping quantity
DEFAULT_QUANT = 1000

def makesoup(url):
    """ This function makes a soup object

    This function takes a url and returns a BeautifulSoup object from it containing webpage html
    :url: str; contains webpage
    """
    html = r_sesh.get(url).content
    return BeautifulSoup(html,"lxml")

def scrape_links(quant=DEFAULT_QUANT):
    """ Create the master list of recipes
    
    Creates an AllRecipeBook instance for allrecipes.com/recipes and returns the created linklist with the desired number of recipes

    Parameter:
        :quant: int, holds the desired number of recipes to scrape
    """
    if quant != float('inf'):
        return AllRecipeBook("https://www.allrecipes.com/recipes/",quant).linklist[:quant]
    return AllRecipeBook("https://www.allrecipes.com/recipes/",quant).linklist

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
    def __init__(self,url,quant):
        self.quant = quant
        self.linklist = []
        self.visited = set()
        # prepopulate visited list with links from previous runs to speed up initial computation
        self.prepopulate_links()
        # if the previous runs haven't scraped sufficient data, add to desired quantity
        if len(self.linklist) < self.quant:
            self.makebook(url)

    def findall(self,soup):
        """ This function returns the next set of subcategories or recipes
        returns a tuple holding names of subcategories/recipes and the associated list of urls

        Parameter:
            :soup: BeautifulSoup object holding url html
        """
        try:
            carousel_links = [l.get("href") for l in soup.body.find_all("a",class_="carouselNav__link recipeCarousel__link")]
            if carousel_links:
                carousel_names = [s.get_text(strip=True) for s in soup.body.find_all("div",class_="carouselNav__linkText")]
                return carousel_names,carousel_links
        except:
            print('Attempted to access empty carousel')
            print(soup.name)
            return -1,-1

        # if no more subcategories to travel down, find all recipe card links
        try:
            card_links = [l.get('href') for l in soup.body.find_all("a",class_="card__titleLink manual-link-behavior")]
            return None,card_links
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
        # if the desired quantity has been reached, end
        if len(self.linklist) > self.quant:
            return

        # if url is gallery type, then skip completely
        if url.find("https://www.allrecipes.com/gallery/") != -1:
            return

        # if url is in linklist, then skip completely
        if url in self.linklist:
            return

        # create soup for current url page
        soup = makesoup(url)
        soup.name = url

        # figure out whether there are subcategories and get list, otherwise, get list of recipes
        names,links = self.findall(soup)

        # if returns -1, then skip completely
        if names == -1:
            return

        # if subcategories exist, iterate through all and process each
        if names is not None:
            for name,sub in zip(names,links):
                if name not in self.visited:
                    self.visited.add(name)
                    self.makebook(sub)

        # if no more subcategories, gather all recipe links
        else:
            for l in links:
                if link not in self.linklist:
                    self.linklist.append(link)
                    self.save_link(link)

    def prepopulate_links(self,num=0,stop=None):
        """ If "links.txt" exists, prepopulates master lists to avoid unnecessary complications
        
        This function takes in the visited list and linklist and appends every link stored in
        "links.txt"

        Parameters:
            :num: int; holds starting line number, 0 by default
            :stop: int; holds the ending line number, None by default
        """
        with open('links.txt','r') as f:
            for i in range(num):
                f, next()
            for i,line in enumerate(f):
                if stop != None:
                    if i >= stop:
                        f.close()
                        return
                self.linklist.append(str(line).strip())
            f.close()

    def save_link(self,link):
        """ This function handles writing of data to "links.txt"

        Parameter:
            :link: str; contains recipe url
        """
        with open('links.txt','a') as f:
            f.write('{}\n'.format(link))
            f.close()

class Recipe:
    """ Data store for important features of a recipe

    This class leverages Beautiful soup to scrape a recipe webpage, extracting useful features for later processing

    Attributes:
        :soup: BeautifulSoup; holds the object reference to the page html
        :name: string; holds the title of the recipe
        :rating: float; holds the average rating of the recipe
        :ingredients: set; holds all of the listed ingredients of recipe as well as their quantities
        :nutrition: dict; holds nutrition name:value pairs

    Methods:
        :getname: returns a string holding title of the recipe
        :getstars: returns a float holding average 5-star rating
        :getstuff: returns a set of ingredients listed in the recipe
        :getnutri: returns a dict of nutrition name;value pairs 
        :geterr: returns a boolean indicating if any scraping error occured
    """
    def __init__(self,url,debug=False):
        self.__debug = debug
        self.__soup = makesoup(url)
        self.name = self.getname()
        self.rating = self.getstars()
        self.ingredients = self.getstuff()
        self.nutrition = self.getnutri()
        self.__soup.decompose()
    
    def getname(self):
        """ This function fetches the name of the recipe

        Returns a string containing the name of the current recipe
        """
        # attempt to scrape recipe title, otherwise return None
        try:
            name = self.__soup.find("h1",class_='headline heading-content').get_text(strip=True)
        except:
            if self.__debug:
                print("Error getting name")
            return None
        if name:
            return name
        else:
            if self.__debug:
                print("Empty name")
            return None

    def getstars(self):
        """ This function fetches the average 5-star rating of the recipe

        Returns a string with the average 5-star rating
        """
        # extract average ratings value if possible, otherwise return None
        try:
            stars = float(self.__soup.body.find(attrs={"data-ratings-average":True})['data-ratings-average'])
            return stars
        except:
            if self.__debug:
                print("Error getting rating")
            return None

    def getstuff(self):
        """ This function fetches the listed ingredients of the recipe
        returns a set containing the listed ingredients
        """
        # initialize output set of ingredients
        out = set()

        # try to scrape for all ingredients, otherwise return None
        try:
            ings = [s.get_text(strip=True) for s in self.__soup.body.find_all("span",class_='ingredients-item-name')]

            # iterate over all ingredients and clean the string of extraneous wording
            for ing in ings:
                # if any string contains non-ascii characters, replace them
                if not ing.isascii():
                    ing = self.convertedstr(ing)
                # call cleaning routine and add output string to set of ingredients, otherwise return None for error
                out.add(self.cleaning(ing))

            return out
    
        except:
            if self.__debug:
                print("Error getting ingredients")
            return None
        # if scrape succeds but empty, return None
        if not ings:
            if self.__debug:
                print("Empty ingredients")
            return None

    def convertedstr(self,string):
        """ This function cleans a string

        Takes a string containing non-ascii characters and returns the string with numerals replaced by fractions and alphabetics replaced by corresponding ascii equivalents

        Parameter:
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
            '\u0026':'&',
            '-':' '
        }

        for ch in string:
            if ch in unwanted.keys():
                out.append(unwanted[ch])
            else:
                out.append(ch)
        return "".join(out);

    def cleaning(self,ing):
        """ This function takes a string and extracts the base ingredient
        
        Analyzes the parts of speech in ingredient string and returns the substring which holds the base ingredient

        Parameter:
            :ing: str, holds the ingredient string
        """
        # if found certain keywords, parse them out
        keys = [
            '\([\w ]*\)',
            '[Oo]ptional',
            '[Wa]rm',
            '[Rr]oom [Tt]emperature',
            '[Pp]ackage',
            '[Ss]tiffly [Bb]eaten',
            '[Ff]rying',
            '[Tt]ablespoons?',
            '[Tt]easpoons?',
            '[Ss]uch'
        ]
        for key in keys:
            r = search(key,ing)
            if r:
                if r.group(0)[0] != '(':
                    ing = ing[:r.start()] + ing[r.end():]
                ing = ing[:r.start()] + 'of' + ing[r.end():]

        # initialize a list with parts of speech tuples for each word in the ingredient string and reverse it to process it backwards
        w = tb(ing).tags
        w.reverse()

        # check if only one noun, in which case return just the noun
        nouns = ['NN','NNS','NNP']
        ncount = []
        for val,part in w:
            if part in nouns:
                ncount.append(val+' ')
        if len(ncount) == 1:
            return ''.join(ncount)

        # initialize a noun counter and a temp store for words as well as a store for the previous part of speech
        ncount = 0
        temp = []
        prev = None

        # for each word, check if matches conditions at which base ingredient identified, if none satisfied, update prev
        for val,part in w:
            if part == 'CD':
                if prev == 'JJ' or prev == 'N2' or (prev in nouns and ncount>1):
                    temp.pop()
                temp.reverse()
                return ''.join(temp)
            elif prev == 'JJ':
                if ncount > 0:
                    temp.reverse()
                    return ''.join(temp)
            elif part in nouns:
                temp.append(val+' ')
                ncount += 1
                if prev in nouns:
                    prev = 'N2'
            elif part == 'JJ':
                temp.append(val+' ')

            if prev != 'N2':
                prev = part 

    def getnutri(self):
        """ This function fetches the nutrition facts of the recipe

        Returns a dictionary of key:value pairs containing nutrition info
        """
        # initialize output dictionary and initiliaze name:value pairs if possible
        out = {}
        try:
            pairs = [s.get_text(strip=True) for s in self.__soup.find_all("span",class_='nutrient-name')]
            names = [s[:s.find(':')] for s in pairs]
            vals = [s[s.find(':')+1:] for s in pairs]
       
            # if no error, standardize names, record the pairs in dictionary and return
            self.standardize(names,vals)
            for name,val in zip(names,vals):
                out[name] = val
            return out

        except:
            if self.__debug:
                print("Problem getting nutrition")
            return None

    def standardize(self,names,vals):
        """ This function regularizes nutrition names

        Ensures that seperate nutrition factsheets are mapped to the same model and returns the standardized name,val pairs

        Parameters:
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
            "niacin equivalents":"Niacin",
            "niacin equivilants":"Niacin",
            "vitamin b6":"Vitamin B6",
            "magnesium":"Magnesium",
            "folate":"Folate",
            "vitamin c":"Vitamin C",
            "calories from fat":"Cals from Fat"
        }
        # for items already in names, make sure it is standardized value
        for i,name in enumerate(names):
            if standard.get(name.lower()):
                names[i] = standard.get(name.lower())
        # for items not in names, remove
        for diff in set(names).difference(standard.values()):
            idx = names.index(diff)
            names.remove(diff)
            vals.remove(vals[idx])

    def geterr(self):
        """ This function reports if any error occurred in scraping process

        Returns boolean should any attribute return None or if any ingredient in the list is None
        """
        if None in self.ingredients:
            if self.__debug:
                print('Empty ingredient pulled')
            return True
        if self.name is None or self.nutrition is None or self.rating is None or self.ingredients is None:
            return True
        return False
