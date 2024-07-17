# Imports
import pandas as pd
import requests
import chardet
import re
from pathlib import Path

# Creates DataFrame then saves new articles to given file
def create_df_and_output(source, title_list, date_list, link_list, content_list, tags_list, path):
    source_list = []
    for i in range(len(title_list)):
        source_list.append(source)
    df = pd.DataFrame({
        'source': source_list,
        'title': title_list,
        'date': date_list,
        'link': link_list,
        'content': content_list,
        'tags': tags_list
    })

    # Filter for articles not already in the output file
    include_header = False
    try:
        previous_news = pd.read_csv(path, encoding="utf-8-sig")
        for index, row in df.iterrows():
            if (previous_news == row['title']).any().any():
                df.drop(index,inplace=True)
    except FileNotFoundError:
        include_header = True

    if path == "../output/combined_output.csv":
        if Path(path).is_file():
            df.to_csv(path, mode="a", encoding='utf-8-sig', header=False, index=False)
        else:
            df.to_csv(path, mode="a", encoding='utf-8-sig', header=True, index=False)
    else:
        # Save DataFrame to CSV with utf-8 encoding (sig to make sure Windows recognizes it)
        df.to_csv(path, mode="a", encoding='utf-8-sig', header=include_header, index=False)
        if include_header:
            print("Existing file not found: data saved to new file.")
        elif len(df) == 0:
            print("No new articles found.")
        else:
            print("Existing file found: file updated with new data.")

# Website Fetcher ------------------------------
# Checks for the given website's preferred encoding method to make sure everything is decoded properly
def fetch_and_decode(url):
    response = requests.get(url)
    detected_encoding = chardet.detect(response.content)['encoding']
    if detected_encoding is None:
        detected_encoding = 'utf-8'  # Fallback to utf-8 if no encoding is detected
    return response.content.decode(detected_encoding, errors='ignore')

# Keyword Filter -------------------------------
def company_filter(content):
    all_tags = [] # List of tags for an article
    company_dfs = {
    "Lithium": pd.read_excel("../data/newcompanies.xlsx","Lithium"),
    "Rare Earths": pd.read_excel("../data/newcompanies.xlsx","Rare Earths"),
    "Cobalt": pd.read_excel("../data/newcompanies.xlsx","Cobalt"),
    "Graphite": pd.read_excel("../data/newcompanies.xlsx","Graphite"),
    "Nickel": pd.read_excel("../data/newcompanies.xlsx","Nickel")
    }

    for mineral,df in company_dfs.items():
        for index, row in df.iterrows(): # Iterate through keyword DataFrame
            tag_list = row.search.split(",") # Get list of tags for each company
            for tag in tag_list:
                tag = tag.strip().split("+") # Check for dual-search tags
                if len(tag) > 1: # If dual-search tag, search for both
                    if re.search(fr'\b{tag[0].strip()}\b'.lower(), content.lower()) and re.search(fr'\b{tag[1].strip()}\b'.lower(), content.lower()):
                        all_tags.append(mineral + ":" + row.company.replace(u'\xa0', u' '))
                        break
                # Since "Mineral Resources" and "Anchor" are also common words, must be capitalized
                elif tag[0].strip() == "Mineral Resources" or tag[0].strip() == "Anchor":
                    if re.search(fr'\b{tag[0]}\b', content):
                        all_tags.append(mineral + ":" + row.company.replace(u'\xa0', u' '))
                        break
                else:
                    if re.search(fr'\b{tag[0].strip()}\b'.lower(), content.lower()):
                        all_tags.append(mineral + ":" + row.company.replace(u'\xa0', u' '))
                        break

    if len(all_tags) == 0: # If no tags were found, signify no results
        return ["no results"]
    else: # If here, at least one tag was found, so return the article's tags list
        return all_tags