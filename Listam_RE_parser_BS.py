import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import os.path


transactions = {'Առաջարկում եմ', 'Փնտրում եմ', 'Կփոխանակեմ'}

# The following 2 functions provide standart approach to access clean texts from
# either 1 element or multiple elements via path, ensuring uninterrupted run in
# case individual pages do not have one of the elements or attributes.
def lookup_el(soup, path):
    try:
        return soup.select(path)[0].get_text('\n').lstrip('= -@')
    except IndexError:
        pass

def lookup_els(soup, path):
    return [el.get_text('\n').lstrip('= -@') for el in soup.select(path)]

# This function runs the search with the given filters and collects all the
# individual announcement links from the search results (called from parse
# function below)
def get_links(template, category, filters, headers):
    df = pd.DataFrame(template)
    page_num = 1
    links = []
    while True:
        page_url = 'https://www.list.am/category/{}/{}?'.format(category, page_num) + '&gl=1'
        response = requests.get(page_url, headers=headers, params=filters)
        if f'category/{category}?' in response.url:
            break
        soup = BeautifulSoup(response.text, 'html.parser')
        listings = soup.select('div#contentr > div.dl > div.gl a')
        links += ['https://www.list.am' + el['href'] for el in listings]
        page_num += 1
    
    for i in range(len(links)):
        df.loc[i, 'Հղում'] = links[i]
    
    return df

# Parses individual announcement pages and writes the resulting database to Excel.
def parse(template, filename, category, filters, headers):
    
    # This part can work both from scratch, calling get_links, or update an existing/incomplete
    # database (if an Excel file with the same name already in the same location).
    if os.path.isfile(filename):
        parse.df = pd.read_excel(filename)
        parse.df = parse.df.set_index(parse.df.columns[0])
    else:
        parse.df = get_links(template, category, filters, headers)

    # All potential standard attributes appearing in the attributes table and in the
    # announcement footer.
    group_attrs = {'Տեսակը', 'Շինության տիպը', 'Նորակառույց', 'Վերելակ',
                   'Հարկերի քանակ', 'Հարկ', 'Սենյակների քանակ',
                   'Սանհանգույցների քանակ', 'Ընդհանուր մակերեսը',
                   'Հողատարածքի մակերեսը', 'Առաստաղի բարձրությունը',
                   'Պատշգամբ', 'Վերանորոգում', 'Հայտարարության համարը',
                   'Ամսաթիվ', 'Թարմացվել է'}

    # info fields and corresponding paths, for categories whose path appears only once on a page and
    # which do not require additional processing before writing into the dataframe.
    val_paths = {'Վերնագիր': 'div.vih > h1',
                 'Շտապ': 'div#abar span.ulabel',
                 'Կոդ': 'div#abar span[class="clabel k"]',
                 'Հասցե': 'div#abar div.loc',
                 'Տեքստ': 'div.vi > div.body',
                 'Օգտատեր': 'div#uinfo div a.n',
                 'Օգտատիրոջ մասին': 'div#uinfo div.desc'}

    # Excluding already parsed pages.
    idx = parse.df.index[parse.df['Status'] != 'Done']
    print(len(idx))
    for i in idx:
        link = parse.df.loc[i, 'Հղում']
        try:
            r = requests.get(link, headers=headers)
            if r.status_code != 200:
                parse.df.loc[i, 'Status'] = r.status_code
                continue
        except Exception as err:
            parse.df.loc[i, 'Status'] = err
            continue
            
        s = BeautifulSoup(r.text, 'html.parser')
        
        for key in val_paths:
            parse.df.loc[i, key] = lookup_el(s, val_paths[key])
            
        path_els = lookup_els(s, 'ol > li')
        path = ' > '.join(path_els[1:])
        parse.df.loc[i, 'Կատեգորիա'] = path
        
        price = lookup_el(s, 'div#abar span.price')
        parse.df.loc[i, 'Գին'] = price
        if isinstance(price, str):
            if 'ամսական' in price:
                parse.df.loc[i, 'Վճարման եղանակ'] = 'ամսական'
            elif 'օրական' in price:
                parse.df.loc[i, 'Վճարման եղանակ'] = 'օրական'            

        clabels = lookup_els(s, 'div#abar span.clabel')
        for transaction in transactions:
            if transaction in clabels:
                parse.df.loc[i, 'Գործարքի տեսակ'] = transaction
                break
        if 'Գործակալություն' in clabels:
            parse.df.loc[i, 'Հեղինակ'] = 'Գործակալություն'
        else:
            parse.df.loc[i, 'Հեղինակ'] = 'Անհատ'

        attr_names = lookup_els(s, 'div#attr div.t')
        attr_values = lookup_els(s, 'div#attr div.i')
        attrs = dict(zip(attr_names, attr_values))
        footer = lookup_els(s, 'div.footer > span')
        for item in footer:
            attr_name, attr_value = item.split(': ')
            attrs[attr_name] = attr_value
        
        for attr in group_attrs:
            if attr not in template:
                continue
            else:
                if attr in attrs:
                    parse.df.loc[i, attr] = attrs[attr]
        
        parse.df.loc[i, 'Օգտատիրոջ էջ'] = 'https://www.list.am' + s.select('div#uinfo div a.n')[0]['href']
        parse.df.loc[i, 'List.am-ում է'] = s.select('div#uinfo div.since')[0].text[-10:]
        stars = s.select('div#uinfo a[class="stars h"]')
        try:
            parse.df.loc[i, 'Գնահատական'] = stars[0]['title'].split(': ')[1]
        except IndexError:
            pass
        reviews = s.select('div#uinfo div.i')
        try:
            parse.df.loc[i, 'Կարծիքներ'] = reviews[0].text.split(' ')[0]
        except IndexError:
            pass
        
        # Marking the line/announcement Status as <Done> if all fields are successfully parsed.
        parse.df.loc[i, 'Status'] = 'Done'
        print(i)

    parse.df.to_excel(filename, freeze_panes=(1, 1))
        

if __name__ == '__main__':

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'}
    
    results = {'Հղում': [], 'Status': [], 'Կատեգորիա': [], 'Հեղինակ': [],
                'Գործարքի տեսակ': [], 'Շտապ': [], 'Վերնագիր': [], 'Գին': [],
                'Վճարման եղանակ': [], 'Կոդ': [], 'Հասցե': [], 'Տեսակը': [],
                'Շինության տիպը': [], 'Նորակառույց': [], 'Վերելակ': [],
                'Հարկերի քանակ': [], 'Հարկ': [], 'Սենյակների քանակ': [],
                'Սանհանգույցների քանակ': [], 'Ընդհանուր մակերեսը': [],
                'Հողատարածքի մակերեսը': [], 'Առաստաղի բարձրությունը': [],
                'Պատշգամբ': [], 'Վերանորոգում': [], 'Տեքստ': [],
                'Հայտարարության համարը': [], 'Ամսաթիվ': [], 'Թարմացվել է': [],
                'Օգտատեր': [], 'Օգտատիրոջ էջ': [], 'List.am-ում է': [],
                'Օգտատիրոջ մասին': [], 'Գնահատական': [], 'Կարծիքներ': [],
                }
    
    # filters = {'cmtype': 2, 'type': 1, 'po': 1, 'price1': 50000,
    #         'price2': 70000, 'n': 8, 'crc': -1, '_a5': 3, '_a39': 2,
    #         '_a11_1': 2, '_a11_2': 10, '_a4': 0, '_a37': 0, '_a3_1': 30,
    #         '_a3_2': 70, '_a38': 0}

    category = 54
    
    filters = {'n': 1}

    start = time.time()
    parse(results, 'Yerevan_all.xlsx', category, filters, headers)
    dur = time.time() - start
    print(dur)