    # initialize dataframe initially with only title and rating
    df = pd.DataFrame(columns=["Recipe Title","Rating","Ingredients"])

    # iterate over every recipe url, create a Recipe object, and add the title and rating to the dataframe
    for num,recipe_url in enumerate(book):
        r = Recipe(recipe_url)
        df.loc[num] = [r.name] + [r.rating] + [r.nutrition]
        pd.concat([df,pd.DataFrame(r.nutrition)],axis=1)

    # create a dataframe of ingredients in preparation for one-hot encodings
    ing_list = df.Ingredients.apply(lambda x: list(x))
    ing_df = pd.DataFrame({"Ingredients":ing_list})

    # create a MultiLabelBinarizer and transform ingredients into encodings
    mlb = MultiLabelBinarizer()
    ing_encodings = pd.DataFrame(mlb.fit_transform(ing_df["Ingredients"]),columns=mlb.classes_)

    # concatenate ingredients encodings to dataframe
    df_with_encodings = pd.concat([df,ing_encodings],axis=1)

    # Write the dataframe into an excel sheet for easier access 
    writer = pd.ExcelWriter('recipes.xlsx',engine='xlsxwriter')
    df.to_excel(writer,sheet_name='Sheet1',index=False)
    writer.save()
