import pandas as pd
from foodscrape.scraping import Recipe
from foodscrape.scraping import prepopulate_links
from sklearn.preprocessing import MultiLabelBinarizer

N = 1000

def makeFrame(linenum):
    """ This function makes a recipe dataframe

    This function uses foodscrape to extract recipe data from a list of allrecipes.com recipe urls
    :linenum: int; holds starting line to begin processing
    """
    # initialize the master list of urls
    book = []
    prepopulate_links(book,linenum,N)
    # initialize dataframe initially with only title, rating, and ingredients
    df = pd.DataFrame(columns=["Recipe Title","Rating","Ingredients"])
    # iterate over every recipe url, create a Recipe object, and add the title and rating to the dataframe
    for num,recipe_url in enumerate(book):
        r = Recipe(recipe_url)
        if r.err:
            continue
        df.loc[num] = [r.name] + [r.rating] + [r.ingredients]
        pd.concat([df,pd.DataFrame(r.nutrition)],axis=1)
        print(num)
    return df

def make_one_hots(df):
    """ This function encodes recipe ingredients into one-hot encodings

    This function takes a recipe DataFrame, creates a dictionary of ingredients, and uses it to create one-hot encodings for each
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

def toxl(df,filename):
    """ This function exports data to excel
    
    Writes the given DataFrame into an excel sheet
    :df: DataFrame; holds features for all processed recipes
    :filename: string; holds the name of the output file
    """
    writer = pd.ExcelWriter(filename,engine='xlsxwriter')
    df.to_excel(writer,sheet_name='Sheet1',index=False)
    writer.save()

def encode():
    """ This function converts recipe urls into encoded feature vectors

    This function creates a DataFrame with recipe data, then one-hot encodes the DataFrame, and then
    sends it to excel
    """
    for i in range(0,28):
        df = makeFrame(N*i)
        encoded_df = make_one_hots(df)
        toxl(encoded_df,'recipes{}.xlsx'.format(N*i))

if __name__ == "__main__":
    encode()