from pytesseract import image_to_string
from PIL import Image
import pyscreenshot
import time
import string
import re
import requests
from bs4 import BeautifulSoup
import wikipedia
from collections import Counter

#test

# hard code stop words for time-saving
regex = re.compile('[%s]' % re.escape(string.punctuation))
STOP_WORDS= {'a',
 'about',
 'above',
 'after',
 'again',
 'against',
 'ain',
 'all',
 'am',
 'an',
 'and',
 'any',
 'are',
 'aren',
 "aren't",
 'as',
 'at',
 'be',
 'because',
 'been',
 'before',
 'being',
 'below',
 'between',
 'both',
 'but',
 'by',
 'can',
 'couldn',
 "couldn't",
 'd',
 'did',
 'didn',
 "didn't",
 'do',
 'does',
 'doesn',
 "doesn't",
 'doing',
 'don',
 "don't",
 'down',
 'during',
 'each',
 'few',
 'for',
 'from',
 'further',
 'had',
 'hadn',
 "hadn't",
 'has',
 'hasn',
 "hasn't",
 'have',
 'haven',
 "haven't",
 'having',
 'he',
 'her',
 'here',
 'hers',
 'herself',
 'him',
 'himself',
 'his',
 'how',
 'i',
 'if',
 'in',
 'into',
 'is',
 'isn',
 "isn't",
 'it',
 "it's",
 'its',
 'itself',
 'just',
 'll',
 'm',
 'ma',
 'me',
 'mightn',
 "mightn't",
 'more',
 'most',
 'mustn',
 "mustn't",
 'my',
 'myself',
 'needn',
 "needn't",
 'no',
 'nor',
 'not',
 'now',
 'o',
 'of',
 'off',
 'on',
 'once',
 'only',
 'or',
 'other',
 'our',
 'ours',
 'ourselves',
 'out',
 'over',
 'own',
 're',
 's',
 'same',
 'shan',
 "shan't",
 'she',
 "she's",
 'should',
 "should've",
 'shouldn',
 "shouldn't",
 'so',
 'some',
 'such',
 't',
 'than',
 'that',
 "that'll",
 'the',
 'their',
 'theirs',
 'them',
 'themselves',
 'then',
 'there',
 'these',
 'they',
 'this',
 'those',
 'through',
 'to',
 'too',
 'under',
 'until',
 'up',
 've',
 'very',
 'was',
 'wasn',
 "wasn't",
 'we',
 'were',
 'weren',
 "weren't",
 'what',
 'when',
 'where',
 'which',
 'while',
 'who',
 'whom',
 'why',
 'will',
 'with',
 'won',
 "won't",
 'wouldn',
 "wouldn't",
 'y',
 'you',
 "you'd",
 "you'll",
 "you're",
 "you've",
 'your',
 'yours',
 'yourself',
 'yourselves'}
CAP_STOP_WORDS = {s.capitalize() for s in STOP_WORDS}

def crop_image(img_path, save_file=False):
    im = Image.open(img_path)
    im_width, im_height = im.size
    margin_width = int(im_width/15.)
    top = int(.17*im_height)
    bottom = int(.35*im_height)
    final_shape = (margin_width, top, im_width - margin_width, bottom)
    new_im = im.crop(final_shape)
    if save_file:
        out_path = img_path.split('.')[0] + '_cropped.' + img_path.split('.')[1]
        new_im.save(out_path)
    return new_im

def get_screenshots():
    qbox = (50,170,450,350)
    box_a1 = (60,355,440,425)
    box_a2 = (60,435,440,505)
    box_a3 = (60,520,440,590)
    im_q = pyscreenshot.grab(bbox=qbox)
    im_a1 = pyscreenshot.grab(bbox=box_a1)
    im_a2 = pyscreenshot.grab(bbox=box_a2)
    im_a3 = pyscreenshot.grab(bbox=box_a3)
    return im_q, im_a1, im_a2, im_a3

def get_all_texts():
    return list(map(image_to_string, get_screenshots()))

def clean_text(txt):
    # get rid of stop words
    s = ' '.join([
                word for word
                in txt.split() if word
                not in STOP_WORDS.union(CAP_STOP_WORDS)
                ])
    # get rid of punctuation, special characters, etc
    s = re.sub(r'([^\s\w]|_)+', '', s)
    # s=regex.sub('', s)
    return s

def get_clean_texts():
    texts = list(map(clean_text, get_all_texts()))
    print(texts)
    return texts

def get_text_combos():
    q, a1, a2, a3 = get_clean_texts()
    def f(t1, t2):
        return t1 + ' ' + t2
    return [(q, a1, a2, a3), (f(q, a1), f(q, a2), f(q,a3))]



################
def fetch_results(search_term='apple', number_results=3, language_code='en'):
    import requests
    escaped_search_term = search_term.replace(' ', '+')
    google_url = 'https://www.google.com/search?q={}&num={}&hl={}'.format(
                                                                    escaped_search_term,
                                                                    number_results,
                                                                    language_code
                                                                    )
    response = requests.get(google_url)
    response.raise_for_status()

    return search_term, response.text

def parse_results(html, keyword):
    soup = BeautifulSoup(html, 'html.parser')

    found_results = []
    rank = 1
    result_block = soup.find_all('div', attrs={'class': 'g'})
    for result in result_block:
        try:
            link = result.find('a', href=True)
            title = result.find('h3', attrs={'class': 'r'})
            title = title.get_text()
            desc = result.find('span', attrs={'class': 'st'})
            desc = desc.get_text()
        except:
            continue
        if link and title:
            link = link['href']
            if link != '#':
                found_results.append({'keyword': keyword, 'rank': rank, 'title': title, 'description': desc})
                rank += 1
    return found_results

def scrape_google(search_term, number_results=100, language_code='en'):
    keyword, html = fetch_results(search_term, number_results, language_code)
    results = parse_results(html, keyword)
    return results

#####

def get_wiki_content(page_name):
    return wikipedia.page(page_name).content

def get_all_descriptions(results):
    all_descs = ' '.join([r['description'] for r in results]).replace('\n', ' ')
    return all_descs

def count_occurences(strng, substrings):
    counter = {}
    for substring in substrings:
        counter[substring] = strng.count(substring.lower())
        split_subs = substring.split()
        if len(split_subs) > 1:
            for s in split_subs:
                counter[substring]+= strng.count(s.lower())
    return counter

def google_texts():
    texts = get_clean_texts()
    results = scrape_google(texts[0])
    descs = get_all_descriptions(results)
    clean_descs = clean_text(descs).lower()
    count_data = count_occurences(clean_descs, texts[1:]).items()
    col_width = max(len(k[0]) for k in count_data) + 2
    print('\nTerm'.ljust(col_width), '|Count |Stars')
    print('-'*(col_width+30))
    for k, v in count_data:
        print (k.ljust(col_width)+'|'+str(v).ljust(6)+'|', '*'*v)
    top_terms = Counter(clean_descs.split()).most_common(10)
    print('')
    for k, v in top_terms:
        print(k,v)

def run_it():
    while True:
        trigger = input("\nHit space to run\n")
        google_texts()
