import datetime
import requests
import os
import time
import pandas as pd
from requests_html import HTML


####  Constants  ####
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')
PARSE_DIR = os.path.join(BASE_DIR, 'parse')

now = datetime.datetime.now()
year = now.year

def url_to_txt(url, filename = "pkmnstats.html", save=False):
    # Checks to see if the request goes through without errors
    # Returns text if no errors, otherwise empty string
    r = requests.get(url)
    #print(r)
    if r.status_code == 200:
        html_text = r.text
        if save:
            with open(f"stats-{year}.html", 'w') as f:
                f.write(html_text)
        return html_text
    return ""

def parse_and_extract(url, name):
    # Parses 'meta' table to get statistics and saves it to a csv
    html_text = url_to_txt(url)

    r_html = HTML(html=html_text)
    table_class = ".meta"
    r_table = r_html.find(table_class)
    table_data = []
    header_names = []
    #print(r_table)
    if len(r_table) == 1:
        parsed_table = r_table[0]
        rows = parsed_table.find("tr")
        header_row = rows[0]
        header_cols = header_row.find("th")
        header_names = [x.text for x in header_cols]
        
        for row in rows[1:]:
            #print(row.text)
            cols = row.find("td")
            row_data = []
            for i, col in enumerate(cols):
                #print(i, col.text, '\n\n')
                row_data.append(col.text)
            table_data.append(row_data)
    df = pd.DataFrame(table_data, columns=header_names)
    path = os.path.join(BASE_DIR, 'data')
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join('data', f'{name}.csv')
    df.to_csv(filepath, index=False)

def grab_urls(url):
    # Grabs URL on the limitless TCG completed tournament standings for metagame
    html_text = url_to_txt(url)
    stat_links = []
    r_html = HTML(html=html_text)
    links = r_html.links
    for link in links:
        if "/standings" in link:
            link = link[:-9]
            absolute = "https://play.limitlesstcg.com" + link + "metagame"
            stat_links.append(absolute)
    return stat_links

def get_name(url):
    # Gets the name of the tournament
    html_text = url_to_txt(url)
    if html_text == "":
        return "No Metadata Stats"   
    r_html = HTML(html=html_text)
    table_class = ".name"
    r_table = r_html.find(table_class)
    if "/" in r_table[0].text:
        return "Inproper Named Tournament"
    return r_table[0].text




def clean_col(row):
    score = row['Score']
    numbers = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
    wins = ''
    loss = ''
    ties = ''
    temp = ''
    count = 1
    for char in score:
        if count == 1 and char in numbers:
            wins = wins + char             
        elif count == 2 and char in numbers:
            loss = loss + char
        elif count == 3 and char in numbers: 
            ties = ties + char
        else:
            temp = temp + char
        if temp == ' - ':
            count += 1
            temp = ''

    row['Wins'] = int(wins)
    row['Loss'] = int(loss)
    row['Tie'] = int(ties)
    return row

        
def intial_df_to_csv(filename): 
    # Creates the intial dataframe and saves it to a csv
    my_data = os.path.join(DATA_DIR, filename)
    df = pd.read_csv(my_data)
    df.drop('Unnamed: 0', axis=1, inplace=True)
    df = df.apply(clean_col, axis=1)
    df.drop('Score', axis=1, inplace=True)
    df["Player Count"] = df["Unnamed: 1"]
    df.drop('Unnamed: 1', axis=1, inplace=True)
    df['Share'] = df['Player Count'] / df['Player Count'].sum()
    df['Win %'] = df['Wins'] / (df['Wins'] + df['Loss'] + df['Tie'])
    path = os.path.join(BASE_DIR, 'cache')
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, 'monthly_deck_stats.csv')
    df.to_csv(filepath, index=False)

def add_doubles(row):
    # Increases counts of duplicate decks creating a total
    for key2,row2 in df.iterrows():
        if row['Deck'] == row2['Deck']:
            row['Wins'] = row['Wins'] + row2['Wins']
            row['Loss'] = row['Loss'] + row2['Loss']
            row['Tie'] = row['Tie'] + row2['Tie']
            row['Player Count'] = row['Player Count'] + row2['Player Count']
            #print(f"{row['Deck']} now has {row['Wins']} wins")
        

    return row

#url = "https://play.limitlesstcg.com/tournament/los-weekly-13/metagame"
url = "https://play.limitlesstcg.com/tournaments/completed?format=standard"
def get_tournaments(url):
    # Gets the tournaments and parses them 
    tournaments = grab_urls(url)
    #print(tournaments)
    for url in tournaments:
        
        name = get_name(url)
        if name == "No Metadata Stats":
            pass
        else:
            try:
                parse_and_extract(url, name)
            except OSError:
                pass
        
        print(f"{name} is done parsing!")
        return name
    
    
#intial_df_to_csv('$250 CASH GGtoor Chill TCG Showdown (Free!).csv')
#print(f"{get_date(url)}")
count = 0

for filename in os.listdir(DATA_DIR):
    if filename.endswith(".csv"):
        if count == 0:
            if filename == "No Metadata Stats.csv":
                pass
            else:
                intial_df_to_csv(filename)
                count = count + 1
                intial_data = os.path.join(CACHE_DIR, 'monthly_deck_stats.csv')
                intial_df = pd.read_csv(intial_data)
        else:
            if filename != "No Metadata Stats.csv":
                my_data = os.path.join(DATA_DIR, filename)

                df = pd.read_csv(my_data)
                df.drop('Unnamed: 0', axis=1, inplace=True)
                df = df.apply(clean_col, axis=1)
                df.drop('Score', axis=1, inplace=True)
                df["Player Count"] = df["Unnamed: 1"]
                df.drop('Unnamed: 1', axis=1, inplace=True)
                df['Share'] = df['Player Count'] / df['Player Count'].sum()
                df['Win %'] = df['Wins'] / (df['Wins'] + df['Loss'] + df['Tie'])
                intial_df
                print(f"IntitalDF: {intial_df.head()}")
                print(f"DF: {df.head()}")
                #intial_df[intial_df.Deck.isin(df.Deck)]
                #print(intial_df[intial_df.Deck.isin(df.Deck)])
                intial_df = intial_df.apply(add_doubles, axis=1)
                intial_df['Share'] = intial_df['Player Count'] / intial_df['Player Count'].sum()
                intial_df['Win %'] = intial_df['Wins'] / (intial_df['Wins'] + intial_df['Loss'] + intial_df['Tie'])
                entire_df = pd.concat([intial_df, df])
                entire_df.drop_duplicates(subset=['Deck'])
                
                os.makedirs(PARSE_DIR, exist_ok=True)
                total_csv = os.path.join(PARSE_DIR, 'totalWL.csv')
                #entire_df.sort_values(by='Win %', ascending=False, inplace=True, ignore_index=True)
                entire_df.to_csv(total_csv)
                print(f"Entire: {entire_df.head()}")
            else:
                pass


    






"""
Player count - Count of all player who played deck
Name - Name of the deck
Wins
Loses
Ties
Win % - wins/total
Top 32 - count of top 32
Top 16 - count of top 16
Top 8 - count of top 8
Top 4 - count of top 4
Second - count of second 
First - count of first
Date - Might not need if data is a collection of tournament results. I would need to find a way to account for length of times for results (ie last 30 days)
(date options: date tied to each tournament then display the results of this in real time in Django)
Tournament - Won't need is data is a collection of tournament results

"""