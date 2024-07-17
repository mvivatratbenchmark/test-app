import streamlit as st

st.title("🎈 My new app")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)
# ================= Imports =================
from bs4 import BeautifulSoup
from common import create_df_and_output, fetch_and_decode, company_filter
from datetime import datetime

# ================= Pre-Scraping Setup =================
# Creating BeautifulSoup object
soup = BeautifulSoup(fetch_and_decode("https://www.survivalinternational.org/news"), "html.parser")

# Lists for DataFrame
title_list = []
date_list = []
link_list = []
content_list = []
tags_list = []

# Method to scrape article text
def getContent(link):
    content = []
    page = fetch_and_decode(link)
    soup = BeautifulSoup(page, "html.parser")

    # Narrow down to area with article text
    content_area = soup.find("article", class_="col-xs-12 col-md-8")
    paragraphs = content_area.find_all("p")

    # Iterate through <p> tags
    for p in paragraphs:
        if p.find_parent('figcaption') or p.find('figcaption'): # If <p> is surrounding a figure caption or being contained by <figcaption>, don't scrape text
            continue
        # If here, check that text is actually from the article (not text)
        if p.parent.name == "article" and "col-xs-12" in p.parent.get("class", []):
            content.append(p.get_text())

    return "\n\n".join(content)

# ==================== Main ====================
def run(path = "../output/survival_international.csv", filter_date = datetime(1111,11,1).date()):
    # Scrape the featured news story
    top_news_content = soup.find("header", class_="hero block-type content-bottom")
    top_news_title_area = top_news_content.find("h2")
    top_news_date = datetime.strptime(top_news_title_area.parent.find("h5").find("mark").get_text(), "%B %d, %Y").date()
    top_news_link = "https://survivalinternational.org" + top_news_content.find("a")['href']
    top_news_content = getContent(top_news_link)
    top_news_tags = company_filter(top_news_content)

    if not top_news_tags[0] == "no results":
        title_list.append(top_news_title_area.find("mark").text)
        date_list.append(top_news_date)
        link_list.append(top_news_link)
        content_list.append(top_news_content)
        tags_list.append(top_news_tags)

    # Scrape the rest of the news stories
    # Can go to 290, manually set as that is the last page
    pages_to_scrape = 20
    print(f"Scraping starting ({pages_to_scrape} pages)")
    for i in range(1,pages_to_scrape+1):
        news_link = "https://www.survivalinternational.org/news/archive?page=" + str(i)
        news_page = fetch_and_decode(news_link)
        news_soup = BeautifulSoup(news_page, "html.parser")

        news_area = news_soup.find("div", class_="news-items")
        article_links = news_area.find_all("a")
        for link_element in article_links:
            title = link_element.find("h3").get_text()
            date = datetime.strptime(link_element.find("time").get_text(), "%B %d, %Y").date()

            if filter_date != datetime(1111,11,1).date(): # If article date is earlier than filter date, break out of loop
                if filter_date > date:             # (assumes that articles are ordered by date)
                    print(f"Article found published on {date}, which is before the filter date {filter_date}. Ending scraping early.")
                    create_df_and_output("Survival International", title_list, date_list, link_list, content_list, tags_list, path)
                    return
                
            link = "https://www.survivalinternational.org" + link_element['href']
            article_content = getContent(link)
            tags = company_filter(article_content)

            if (not tags[0] == "no results") and (not title in title_list): # Also double check for duplicate stories
                title_list.append(title)
                date_list.append(date)
                link_list.append(link)
                content_list.append(article_content)
                tags_list.append(tags)

        print(f"Page {i} scraping complete.")

    # ================= Final Processing and Output =================
    create_df_and_output("Survival International", title_list, date_list, link_list, content_list, tags_list, path)

run()
