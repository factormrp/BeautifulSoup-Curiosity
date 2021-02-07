import pandas as pd
from multiprocessing import Pool
from foodscrape.scraping import Recipe
from foodscrape.scraping import scrape_links
from foodscrape.scraping import DEFAULT_QUANT
from sklearn.preprocessing import MultiLabelBinarizer


def makeFrame(quant=DEFAULT_QUANT,debug=False):
    """ This function makes a recipe dataframe

    Uses foodscrape to extract recipe data and returns a pandas DataFrame containing the data for the specified quantity of recipes

    Parameter:
        :quant: int; holds the number of recipes to attempt to scrape
    """

    # initialize dataframe initially with only title, rating, and ingredients
    df = pd.DataFrame(columns=["Recipe Title","Rating","Ingredients"])
    df_nutri = pd.DataFrame()
        
    print('pulling recipes...')
    # initialize the master list of urls
    book = scrape_links(quant)
    # iterate over every recipe url, create a list of recipes objects
    with Pool(10) as p:
        recipes = p.map(Recipe,book)

        # and add the title and rating to the dataframe. If fails, record corresponding links.txt index num of recipe to error_recipes log file
        if debug:
            with open('error_recipes.txt','w') as f:
                errors = 0
                for num,r in enumerate(recipes):
                    if r.geterr():
                        errors += 1
                        f.write(f'{num}\n')
                        continue
                    df.loc[num-errors] = [r.name] + [r.rating] + [r.ingredients]
                    df_nutri = pd.concat([df_nutri,pd.DataFrame(r.nutrition,index=[num-errors])])
                f.close()
        else: 
            errors = 0
            for num,r in enumerate(recipes):
                if r.geterr():
                    errors += 1
                    continue
                df.loc[num-errors] = [r.name] + [r.rating] + [r.ingredients]
                df_nutri = pd.concat([df_nutri,pd.DataFrame(r.nutrition,index=[num-errors])])
    
    out = pd.concat([df,df_nutri],axis=1)
    return out

def encode(df):
    """ This function encodes recipe ingredients into one-hot encodings

    Takes a pandas DataFrame, creates a dictionary of ingredients, and uses it to create one-hot encodings for each recipe
    
    Parameter:
        :df: DataFrame; holds features for all processed recipes
    """
    # create a dataframe of ingredients in preparation for one-hot encodings
    ing_list = df.Ingredients.apply(lambda x: list(x))
    ing_df = pd.DataFrame({"Ingredients":ing_list})

    # create a MultiLabelBinarizer and transform ingredients into encodings
    mlb = MultiLabelBinarizer()

    ing_encodings = pd.DataFrame(mlb.fit_transform(ing_df["Ingredients"]),columns=mlb.classes_)

    # concatenate ingredients encodings to dataframe
    df_with_encodings = pd.concat([df,ing_encodings],axis=1)

    return df_with_encodings

def excel_export(df,filename):
    """ This function exports data to excel
    
    Writes the given DataFrame into an excel sheet using 

    Parameters:
        :df: DataFrame; holds features for all processed recipes
        :filename: string; holds the name of the output file
    """
    writer = pd.ExcelWriter(filename,engine='xlsxwriter')
    df.to_excel(writer,sheet_name='Sheet1',index=False)
    writer.save()

def to_excel(quant=DEFAULT_QUANT):
    """ This function converts recipe urls into encoded feature vectors

    Creates a pandas DataFrame with recipe data, then one-hot encodes the DataFrame, and then
    sends it to excel

    Parameter:
        :quant: int; stores number of recipes to attempt to scrape
    """
    print('creating df...')
    df = makeFrame(quant)
    print('encoding df...')
    encoded_df = encode(df)
    print('exporting df...')
    excel_export(encoded_df.drop(columns=['Ingredients']),'recipes.xlsx')
