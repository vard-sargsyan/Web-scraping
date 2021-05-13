import requests
import pandas as pd
from bs4 import BeautifulSoup
import re


headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'}

response = requests.get('https://itguide.eif.am/?id=-1#top', headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')


index = pd.Index([], name = 'ID')
columns = pd.Index(['Name', 'Manager', 'Website', 'Description'])
db = pd.DataFrame(index=index, columns = columns)

orgs = soup.select('div#list_div > div.list_item > a')

for org in orgs:
    id = org['name'].lstrip('item_')
    print(id)
    resp = requests.get('https://itguide.eif.am/index.php?id='+id, headers=headers)
    resp_text = resp.text.replace('<br />', '\n')
    resp_text = re.sub('\n\n+', '\n', resp_text)
    resp_text = resp_text.replace('&nbsp;', ' ')
    profile = BeautifulSoup(resp_text, 'html.parser')
    content = profile.find(id='content_div')
    texts = []
    for el in content:
        try:
            text = re.sub('\n\n+', '\n', el.text)
        except AttributeError:
            continue
        els = text.split('\n')
        for text in els:
            text = text.strip()
            if text and text not in texts:
                texts.append(text)
    if not texts:
        continue
    texts.remove('Share')
    texts.remove('|')
    heading = content.find(re.compile('^h'))
    try:
        count = heading.text.count('\n')
    except AttributeError:
        count = 0
    texts = texts[count+1:]
    db.loc[id, 'Name'] = org.text
    db.loc[id, 'Manager'] = texts[0]
    desc = []
    website = []
    for text in texts[1:]:
        if not re.match('(Website: )|(Website http)|(http:)|(https:)|(www.)', text):
            desc.append(text)
        else:
            addrs = [addr.strip() for addr in text.split(',')]
            website.extend(addrs)
            idx = texts.index(text) + 1
            for next in texts[texts.index(text)+1:]:
                if re.match('(Website: )|(Website http)|(http:)|(https:)|(www.)', next):
                    addrs = [addr.strip() for addr in next.split(',')]
                    website.extend(addrs)
                    idx += 1
                else:
                    break
            desc.clear()
            desc.extend(texts[idx:])
            break
    db.loc[id, 'Website'] = '\n'.join(website)
    db.loc[id, 'Description'] = '\n'.join(desc)
    
db.to_excel('EIF.xlsx', freeze_panes=(1, 1))