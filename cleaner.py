from bs4 import BeautifulSoup, Tag
import os
import re

#using lxml parser if available; fallback to html.parser.
try:
    import lxml 
    DEFAULT_PARSER = 'lxml'
except Exception:
    DEFAULT_PARSER = 'html.parser'


def clean_html(html_content):
    """clean html content and return cleaned html string
    """
    soup = BeautifulSoup(html_content, DEFAULT_PARSER)

    for tag_name in ('style', 'head'):
        for tag in list(soup.find_all(tag_name)):
            tag.decompose()

    #move leading text out of <p> elements that also contain images.
    for p in list(soup.find_all('p')):
        imgs = p.find_all('img')
        if not imgs:
            continue

        #build a new paragraph from the leading nodes until the first <img>
        if not p.contents:
            continue

        #if first child is an image or empty, skip
        first = p.contents[0]
        first_is_img = getattr(first, 'name', None) == 'img'
        if first_is_img:
            continue

        new_p = soup.new_tag('p')
        #move leading non-image contents into new_p
        while p.contents and getattr(p.contents[0], 'name', None) != 'img':
            new_p.append(p.contents[0].extract())

        if new_p.get_text(strip=True):
            p.insert_before(new_p)

            #for each image left in p, unwrap any immediate span parents then extract and place after new_p
            for img in list(p.find_all('img')):
                parent_span = img.find_parent('span')
                if parent_span:
                    parent_span.unwrap()
                extracted = img.extract()
                new_p.insert_after(extracted)

        # remove empty paragraphs
        if not p.get_text(strip=True) and not p.find('img'):
            p.decompose()

    #unwrap all span tags once
    for span in list(soup.find_all('span')):
        span.unwrap()

    #attributes to remove
    attributes_to_remove = {'id', 'style', 'title', 'colspan', 'rowspan'}
    for tag in list(soup.find_all(True)):
        # keep 'class' on div tags, otherwise remove 'class'
        if tag.name != 'div' and 'class' in tag.attrs:
            del tag.attrs['class']

        # remove the rest of attributes (if present)
        for attr in attributes_to_remove:
            if attr in tag.attrs:
                del tag.attrs[attr]

    # Remove or unwrap divs: if empty and no images -> decompose, else unwrap
    for div in list(soup.find_all('div')):
        if not div.get_text(strip=True) and not div.find('img'):
            div.decompose()
        else:
            div.unwrap()

    # Clean up <p> tags: remove Updated... headers and empty paragraphs in a single pass
    updated_re = re.compile(r'^Updated\s*\d+', re.IGNORECASE)
    for p in list(soup.find_all('p')):
        text = p.get_text(strip=True)
        if not text:
            p.decompose()
            continue
        if updated_re.search(text):
            p.decompose()

    #remove empty tables
    for table in list(soup.find_all('table')):
        if not table.get_text(strip=True):
            table.decompose()

    #normalize text nodes but avoid replacing every string unnecessarily
    for text_node in list(soup.find_all(string=True)):
        if not text_node or not isinstance(text_node, str):
            continue
        if '\xa0' not in text_node and not re.search(r'\s{2,}', text_node):
            continue
        clean_text = text_node.replace('\xa0', ' ')
        normalized_text = ' '.join(clean_text.split())
        text_node.replace_with(normalized_text)

    #remove empty h1 that may only contain images
    for h1_tag in list(soup.find_all('h1')):
        if not h1_tag.get_text(strip=True) and h1_tag.find('img'):
            h1_tag.unwrap()

    #unwrap body/html if present
    if soup.body:
        soup.body.unwrap()
    if soup.html:
        soup.html.unwrap()

    #wrap all content in a new div with required structure
    new_div = soup.new_tag('div', **{'class': 'article-body'})
    new_h1 = soup.new_tag('h1', **{'class': 'article-title invisible'})
    new_h1.string = 'Title'
    new_p = soup.new_tag('p', **{'class': 'article-summary invisible'})
    new_p.string = 'Summary'
    new_div.append(new_h1)
    new_div.append(new_p)

    #move all remaining top-level content into the new div
    content_to_wrap = list(soup.contents)
    for element in content_to_wrap:
        new_div.append(element)
    soup.clear()
    soup.append(new_div)

    return soup.prettify()