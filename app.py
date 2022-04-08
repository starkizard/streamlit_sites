import streamlit as st
import pandas as pd

st.title("Reykjavik tracker")
# r = requests.get("https://chess-results.com/tnr599063.aspx?lan=1&art=9&fed=JCI&flag=30&snr=240")
# soup = BeautifulSoup(r.content, "lxml")
# dom = etree.HTML(str(soup))
# table =dom.xpath('//*[@id="F7"]/div[2]/table[2]')[0]
# st.markdown(etree.tostring(table), unsafe_allow_html = True)


def display_table(link, name):
    table = pd.read_html(link)
    st.header(name)
    df = table[5].drop([3], axis = 1)
    new_header = df.iloc[0] #grab the first row for the header
    df = df[1:] #take the data less the header row
    df.columns = new_header #set the header row as the df heade
    df = df.dropna(axis = 1, how = "all")
    df.reset_index(drop = True)
    st.write(df)



d = [
    ("Lula" , "https://chess-results.com/tnr599063.aspx?lan=1&art=9&fed=JCI&flag=30&snr=240"),
    ("Jahny" , "https://chess-results.com/tnr599063.aspx?lan=1&art=9&fed=ISL&flag=30&snr=226"),
]


for name, link in d:
    display_table(link, name)
