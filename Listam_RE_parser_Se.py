from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException as NoSuchEl
from selenium.common.exceptions import NoSuchAttributeException as NoSuchAttr
from selenium.common.exceptions import NoSuchWindowException as NoSuchWin
import pandas as pd
import numpy as np
import os.path
import time


driver=webdriver.Chrome()

transactions = {'Առաջարկում եմ', 'Փնտրում եմ', 'Կփոխանակեմ'}

def build_url(category, **filters):
    url = 'https://www.list.am/category/' + str(category) + '/{}?'
    for key in filters:
        url += f'{key}={filters[key]}&'
    url += 'gl=1'
    return url

# The following 2 functions provide standart approach to access either 1 element
# or multiple elements through find-by-xpath methods, simultaneously ensuring
# uninterrupted run in case individual pages do not have one of the elements or
# attributes as well as handling lost connection issues.
def lookup_el(driver, path):
    try:
        return driver.find_element_by_xpath(path).text.lstrip('= ')
    except (NoSuchEl, NoSuchAttr):
        return np.nan
    except NoSuchWin:
        return 'NoSuchWin'

def lookup_els(driver, path):
    try:
        return [node.text for node in driver.find_elements_by_xpath(path)]
    except (NoSuchEl, NoSuchAttr):
        return []
    except NoSuchWin:
        return ['NoSuchWin']

# This function runs the search with the given link constructed with the required
# filters and collects all the individual announcement links from the search results
# (called from parse function below)
def get_links(template, url, category):
    df = pd.DataFrame(template)
    page_num=1
    links = []
    while True:
        page_url = url.format(page_num)
        driver.get(page_url)
        if f'category/{category}?' in driver.current_url:
            break
        listings = driver.find_element_by_xpath("//div[@id='contentr']/div[@class='dl']/div[@class='gl']")
        a_tags = listings.find_elements_by_tag_name('a')
        links += [a_tag.get_attribute('href') for a_tag in a_tags]
        page_num += 1
    
    for i in range(len(links)):
        df.loc[i, 'Հղում'] = links[i]
    
    return df

# Parses individual announcement pages and writes the resulting database to Excel.
def parse(template, filename, url, category):
    
    # This part can work both from scratch, calling get_links, or update an existing/incomplete
    # database (if an Excel file with the same name already in the same location).
    if os.path.isfile(filename):
        parse.df = pd.read_excel(filename)
        parse.df = parse.df.set_index(parse.df.columns[0])
        start = parse.df[parse.df['Status'].isnull()].index[0]
    else:
        parse.df = get_links(template, url, category)
        start = 0
    
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
    val_paths = {'Վերնագիր': "//body//h1",
                 'Շտապ': "//div[@id='abar']//span[@class='ulabel']",
                 'Կոդ': "//div[@id='abar']//span[@class='clabel k']",
                 'Հասցե': "//div[@id='abar']//a",
                 'Տեքստ': ".//div[@Class='body']"}

    # Getting each page link, opening the page, parsing the data and writing into the dataframe
    for i in range(start, len(parse.df)):
        link = parse.df.loc[i, 'Հղում']
        try:
            driver.get(link)
        except NoSuchWin:
            parse.df.loc[i, 'Status'] = 'NoSuchWin'
       
        time.sleep(1)
        for key in val_paths:
            parse.df.loc[i, key] = lookup_el(driver, val_paths[key])
        
        price = lookup_el(driver, "//div[@id='abar']//span[@class='price']")
        parse.df.loc[i, 'Գին'] = price
        if isinstance(price, str):
            if 'ամսական' in price:
                parse.df.loc[i, 'Վճարման եղանակ'] = 'ամսական'
            elif 'օրական' in price:
                parse.df.loc[i, 'Վճարման եղանակ'] = 'օրական'
        
        path_els = lookup_els(driver, "//div[@id='crumb']/ol/li")
        path = ' > '.join(path_els[1:])
        parse.df.loc[i, 'Կատեգորիա'] = path
        
        clabels = lookup_els(driver, "//div[@id='abar']//span[@class='clabel']")
        for transaction in transactions:
            if transaction in clabels:
                parse.df.loc[i, 'Գործարքի տեսակ'] = transaction
                break
        if 'NoSuchWin' in clabels:
            parse.df.loc[i, 'Հեղինակ':'Գործարքի տեսակ'] = 'NoSuchWin'
        if 'Գործակալություն' in clabels:
            parse.df.loc[i, 'Հեղինակ'] = 'Գործակալություն'
        else:
            parse.df.loc[i, 'Հեղինակ'] = 'Անհատ'

        attr_names = lookup_els(driver, ".//div[@id='attr']/div[@Class='c']/div[@Class='t']")
        attr_values = lookup_els(driver, ".//div[@id='attr']/div[@Class='c']/div[@Class='i']")
        attrs = dict(zip(attr_names, attr_values))
        footer = lookup_els(driver, ".//div[@Class='footer']/span")
        if 'NoSuchWin' in attr_names + attr_values + footer:
            parse.df.loc[i, 'Status'] = 'NoSuchWin'
        else:
            for item in footer:
                attr_name, attr_value = item.split(': ')
                attrs[attr_name] = attr_value
            
            for attr in group_attrs:
                if attr not in template:
                    continue
                else:
                    if attr in attrs:
                        parse.df.loc[i, attr] = attrs[attr]
        
        # Marking the line/announcement Status as <Done> if all fields are successfully parsed,
        # or 'NoSuchWin' (the corresponding error note) if there was an error accessing the page/element(s)
        if 'NoSuchWin' in list(parse.df.loc[i]):
            parse.df.loc[i, 'Status'] = 'NoSuchWin'
        else:
            parse.df.loc[i, 'Status'] = 'Done'

    parse.df.to_excel(filename, freeze_panes=(1, 1))


if __name__ == '__main__':
    
    results = {'Հղում': [], 'Status': [], 'Կատեգորիա': [], 'Հեղինակ': [],
                'Գործարքի տեսակ': [], 'Շտապ': [], 'Վերնագիր': [], 'Գին': [],
                'Վճարման եղանակ': [], 'Կոդ': [], 'Հասցե': [], 'Տեսակը': [],
                'Շինության տիպը': [], 'Նորակառույց': [], 'Վերելակ': [],
                'Հարկերի քանակ': [], 'Հարկ': [], 'Սենյակների քանակ': [],
                'Սանհանգույցների քանակ': [], 'Ընդհանուր մակերեսը': [],
                'Հողատարածքի մակերեսը': [], 'Առաստաղի բարձրությունը': [],
                'Պատշգամբ': [], 'Վերանորոգում': [], 'Տեքստ': [],
                'Հայտարարության համարը': [], 'Ամսաթիվ': [], 'Թարմացվել է': []}

    # Filtering approach 1: default filters included
    # category = 60
    
    filters = {'cmtype': 2, 'type': 1, 'po': 1, 'price1': 50000,
                'price2': 70000, 'n': 8, 'crc': -1, '_a5': 3, '_a39': 2,
                '_a11_1': 2, '_a11_2': 10, '_a4': 0, '_a37': 0, '_a3_1': 30,
                '_a3_2': 70, '_a38': 0}

    # Filtering approach 2: only non-default filters included

    category = 60
    
    #filters = {'n': 1}

    url = build_url(category, **filters)    

    parse(results, 'Yerevan_apt_sales_Sel.xlsx', url, category)
    