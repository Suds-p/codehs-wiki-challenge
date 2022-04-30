import re
import sys
import requests
from bs4 import BeautifulSoup as bs, NavigableString

WIKI_URL = 'https://en.wikipedia.org'
MAX_HOPS = 256
hops = 0

###############
#  FUNCTIONS  #
###############
"""
  Determines if a given link goes to a valid Wikipedia page.
  Empty links or links to images, sound files, etc. are ignored.

  @param link 'a' tag element parsed with BeautifulSoup.
  @return True if link is valid; False otherwise.
"""
def link_filter(link):
  if link == "":
    return False
  if re.match(r'/wiki/(Help|File|Wikipedia):.*', link):
    return False
  if re.match(r'.*upload.wikimedia.org.*', link):
    return False
  if 'en.wiktionary.org' in link:
    return False
  return True


"""
  Returns base URL from a given 'a' Tag without any sections in the URL.
  For example, if href was 'http://example.org#Section1', the function 
  will return 'http://example.org'.

  @param a_tag An 'a' tag element parsed with BeautifulSoup.
  @return String coming from href attribute without any hashtag sections.
"""
def extract_link(a_tag):
  return a_tag['href'].split('#')[0]


"""
  Mutates a given BeautifulSoup tag to remove any elements within the first pair
  of parentheses in the tag's contents. The contents are available as a list
  accessible via indexes. The function starts/stops when encountering string 
  elements that contain either '(' or ')'.

  @param elem A BeautifulSoup Tag element.
  @return Same element with contents mutated.
"""
def remove_parens(elem):
  extracting = False

  i = 0
  while i < len(elem.contents):
    child = elem.contents[i]

    if isinstance(child, NavigableString):
      extracting = True if '(' in child else False if ')' in child else extracting
      if ')' in child:
        child.extract()
        break

    if extracting:
      child.extract()
    else:
      # switch to next element
      i += 1
  return elem


"""
  Creates a stream of links from the main section of a Wikipedia article.
  All links can be iterated over using a for loop, or received one at a time
  using the next() function. Example:
  links = get_main_links('https://example.org')
  print(next(links))
  print(next(links))
  ...

  @param link A string URL to a valid Wikipedia article.
  @return Generator object that yields string URLs to each link in the article.
"""
def get_main_links(link):
  page = requests.get(link)
  soup = bs(page.content, 'html.parser')
  main_content = soup.select_one('#mw-content-text .mw-parser-output')
  # Finds all paragraph sections of article, using recursive=False for direct descendants
  sections = main_content.find_all('p', id=False, class_=False, recursive=False)

  # Return all links from each section of article
  for s in sections:
    remove_parens(s)
    links = filter(link_filter, map(extract_link, s.find_all('a')))
    for l in links:
      yield WIKI_URL + l
  yield None # to prevent exceptions from running out of links


"""
  Prints out a path to the "Philosophy" Wikipedia article from the starting
  url provided. Only uses the first link on a given article unless it has 
  been visited. Otherwise, it uses the second link, or the third, etc.

  @param url A string URL to a valid Wikipedia article.  
"""
def get_to_philosophy(start_url):
  # Reset variables
  global hops
  visited = set([start_url])
  url_stack = [{ 'url': start_url, 'links': get_main_links(start_url) }]
  hops = 0

  def recursion_helper(url):
    global hops
    print(url)

    # Base case
    if hops >= MAX_HOPS:
      print(f'\n Too many hops: reached max limit ({hops}) before finding Philosophy')
      return True
    if 'Philosophy' in url:
      print(f'\nSuccessfully found Philosophy in {hops} hops!')
      return True

    current = url_stack.pop()
    next_link = next(current['links'])

    # Recursive case
    while next_link is not None:
      if next_link not in visited:
        hops += 1
        visited.add(next_link)
        url_stack.append({
          'url': next_link,
          'links': get_main_links(next_link)
        })
        halt_program = recursion_helper(next_link)
        if halt_program:
          return True
      
      next_link = next(current['links'])
    
    if next_link == None:
      hops -= 1
  
  recursion_helper(start_url)


###############
#  MAIN LOOP  #
###############
if __name__ == '__main__':
  if len(sys.argv) == 1:
    print('\nNo link provided\nUsage: python getting_to_philosophy.py STARTING_LINK')
    sys.exit(0)
  
  start_url = sys.argv[1]
  if re.match(r'https?://en.wikipedia.org/wiki/.*', start_url):
    if link_filter(start_url.split('/')[-1]):
      get_to_philosophy(start_url)
      sys.exit(0)
  
  print('\nURL provided is not valid:', start_url)