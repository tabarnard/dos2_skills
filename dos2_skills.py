#!/usr/bin/env python3

import requests
import requests_cache
from bs4 import BeautifulSoup
import logging
from collections import OrderedDict
import re
import pandas as pd

# use requests_cache so that we don't overload the wiki while writing this
requests_cache.install_cache('cache')

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_format = '[%(asctime)s] %(levelname)-8s %(message)s'
formatter = logging.Formatter(log_format)
s_handler = logging.StreamHandler()
s_handler.setLevel(logging.DEBUG)
s_handler.setFormatter(formatter)
log.addHandler(s_handler)

def get_soup(url):
    result = requests.get(url)
    log.debug(f'getting soup: url: {url} status_code: {result.status_code}')
    content = result.content
    soup = BeautifulSoup(content, 'html.parser')
    return soup

def get_pairs(soup):
    table_rows = soup.find('table', {'class': 'wiki_table'}).find('tbody').find_all('tr')
    # each skill consists of two rows, so zip them together
    row_pairs = list(zip(table_rows[::2], table_rows[1::2]))
    return row_pairs

schools = {
    'Aerotheurge': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Aerotheurge+Skills'),
    'Geomancer': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Geomancer+Skills'),
    'Huntsman': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Huntsman+Skills'),
    'Hydrosophist': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Hydrosophist+Skills'),
    'Necromancer': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Necromancer+Skills'),
    'Polymorph': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Polymorph+Skills'),
    'Pyrokinetic': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Pyrokinetic+Skills'),
    'Scoundrel': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Scoundrel+Skills'),
    'Summoning': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Summoning+Skills'),
    'Warfare': get_soup('https://divinityoriginalsin2.wiki.fextralife.com/Warfare+Skills'),
}

def get_rows():
    rows = []

    for school, soup in schools.items():
        pairs = get_pairs(soup)
        for r1, r2 in pairs:
            row = OrderedDict()
            row['skill'] = ''
            row['school_a'] = ''
            row['req_a'] = ''
            row['school_b'] = ''
            row['req_b'] = ''
            row['mem'] = ''
            row['ap'] = ''
            row['sp'] = ''
            row['cd'] = ''
            row['resistance'] = ''
            row['scale'] = ''
            row['range'] = ''
            row['description'] = ''
            row['note'] = ''

            # some of the tables have slightly different elements on row 1
            if r1.th:
                skill = r1.find_all('th')[0].text.strip()
                href = r1.find_all('th')[0].find_all('a')[0].attrs['href']
                row['skill'] = f'=HYPERLINK("https://divinityoriginalsin2.wiki.fextralife.com{href}", "{skill}")'
                row['description'] = r1.find_all('td')[0].text.strip()
            else:
                skill = r1.find_all('td')[0].text.strip()
                href = r1.find_all('td')[0].find_all('a')[0].attrs['href']
                row['skill'] = f'=HYPERLINK("https://divinityoriginalsin2.wiki.fextralife.com{href}", "{skill}")'
                row['description'] = r1.find_all('td')[1].text.strip()

            cols = r2.find_all(['th', 'td'])

            # extract the integers for skill requirement
            req = re.findall(r'\d', cols[0].text)

            # pull the school out of the pngs and correct typo
            row['school_a'] = f'{cols[0].find_all("img")[0].attrs["src"].split("/")[-1].split("-")[0].replace("hunstman", "huntsman").title()}'
            row['req_a'] = req[0]
            if len(req) > 1:
                row['school_b'] = f'{cols[0].find_all("img")[1].attrs["src"].split("/")[-1].split("-")[0].replace("hunstman", "huntsman").title()}'
                row['req_b'] = req[1]

            # mem is easy
            row['mem'] = cols[1].text.strip()

            # ap is AP.png, AP1.png, etc.
            # can also be a -, n/a, or blank for 0
            try:
                ap = cols[2].find_all('img')[0].attrs['src'].split('/')[-1].split('.')[0]
                ap = re.sub('^AP$', 'AP1', ap)
                ap = ap.replace('AP', '')
            except IndexError:
                ap = '0'
            row['ap'] = ap

            # sp is similar
            try:
                sp = cols[3].find_all('img')[0].attrs['src'].split('/')[-1].split('.')[0]
                sp = re.sub('^SP$', 'SP1', sp)
                sp = sp.replace('SP', '')
            except IndexError:
                sp = '0'
            row['sp'] = sp

            # a little quirk
            cd = cols[4].text.strip()
            cd = cd.replace('4 (3 in def. Edition)', '3')
            cd = cd.replace('-', '0')
            row['cd'] = cd

            # extract from image, else n/a
            try:
                resistance = cols[5].find_all('img')[0].attrs['src'].split('/')[-1].split('_')[0].title()
            except IndexError:
                resistance = 'n/a'
            row['resistance'] = resistance

            row['scale'] = cols[6].text.strip()
            row['range'] = cols[7].text.strip()
            row['note'] = cols[8].text.strip()

            rows.append(row)

    return rows

def main():
    rows = get_rows()
    df = pd.DataFrame(rows)
    df.to_excel('dos2_skills.xlsx', index=False)

if __name__ == '__main__':
    main()
