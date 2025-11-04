from bs4 import BeautifulSoup, Tag
import os
import re

def clean_html(html_content):
    """
    Cleans and formats HTML
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    #removes the whole <style>
    for style_tag in soup.find_all('style'):
        style_tag.decompose()

    #remove the entire <head> tag
    head_tag = soup.find('head')
    if head_tag:
        head_tag.decompose()

    # #unwrap img tags from their parent span and p tags 
    # for img_tag in soup.find_all('img'):
    #     #unwrap parent span if it exists
    #     parent_span = img_tag.find_parent('span')
    #     if parent_span:
    #         parent_span.unwrap()
        
    #     #unwrap parent p if it exists
    #     parent_p = img_tag.find_parent('p')
    #     if parent_p:
    #         #move clsoingtag in front of image tag
    #         parent_p.unwrap() 



    for img_tag in soup.find_all('img'):
        parent_p = img_tag.find_parent('p')
        if parent_p:
            # Check if the text sibling before the image (ignoring whitespace/newlines)
            # contains the step-like header.
            # We look for a previous text sibling, or a sibling tag (usually span) that contains the text
            
            # Find the element containing the step text, typically the first child of the <p>
            step_text_element = parent_p.contents[0] if parent_p.contents else None
            
            # If the step text and the image are direct children of the same <p>
            if step_text_element and step_text_element != img_tag:
                # Create a new p tag for the step text (or the element containing it)
                new_p = soup.new_tag('p')
                
                # Move the step text element and the image's parent span/p out of the original p
                
                # Unwrap the image's immediate span parent if it exists
                parent_span = img_tag.find_parent('span')
                if parent_span:
                    parent_span.unwrap()

                # Extract the image
                extracted_img = img_tag.extract()
                
                # The remaining content in parent_p is likely the text/span.
                # Use parent_p.contents to get all remaining elements (text/spans)
                content_to_move = list(parent_p.contents)
                for content in content_to_move:
                    new_p.append(content.extract())
                
                # Insert the new p tag with the text before the original p tag (which will now be removed or empty)
                parent_p.insert_before(new_p)
                
                # Insert the extracted image after the new p tag
                new_p.insert_after(extracted_img)
                
                # Clean up the original parent_p if it is now empty (which it should be)
                if not parent_p.get_text(strip=True) and not parent_p.find('img'):
                    parent_p.decompose()

    # 2. Unwrap all span tags while keeping their contents (after the separation above)
    for span in soup.find_all('span'):
        span.unwrap()

    #remove these attributes
    attributes_to_remove = ['id', 'style', 'title', 'class', 'colspan', 'rowspan']
    for tag in soup.find_all(True):
        #keep 'class' on div tags
        if tag.name != 'div' and 'class' in tag.attrs:
            del tag.attrs['class']
        
        # remove the rest
        for attr in attributes_to_remove:
            if attr in tag.attrs and attr != 'class':
                del tag.attrs[attr]

    #Remove all span tags while keeping their contents
    for span in soup.find_all('span'):
        span.unwrap()

    # Remove div tags and their content only if they are empty
    for div in soup.find_all('div'):
        if not div.get_text(strip=True) and not div.find('img'):
            div.decompose()
        else:
            div.unwrap()
    
    #remove any text that inclues 'updated'
    for p_tag in soup.find_all('p'):
        # The regular expression matches "Updated" followed by a number and an optional colon.
        if re.search(r'^Updated\s*\d+', p_tag.get_text(strip=True)):
            p_tag.decompose()

    #removes empty html tables
    for table in soup.find_all('table'):
        if not table.get_text(strip=True):
            table.decompose()
        
    #remove empty p tags
    for p in soup.find_all('p'):
        if not p.get_text(strip=True):
            p.decompose()

    #replace &nbsp; with a regular space
    # attempting to remove extra whitespace
    for text_node in soup.find_all(string=True):
        # 1. Replace non-breaking spaces with standard spaces
        clean_text = text_node.replace("\xa0", " ")
        normalized_text = " ".join(clean_text.split())
        
        text_node.replace_with(normalized_text)


    for h1_tag in soup.find_all('h1'):
        #chekc if emoty and has img
        if not h1_tag.get_text(strip=True) and h1_tag.find('img'):
            h1_tag.unwrap()


    #unwrap body and html tags
    if soup.body:
        soup.body.unwrap()
    if soup.html:
        soup.html.unwrap()

    #make new divs
    new_div = soup.new_tag("div", **{'class': 'article-body'})

    new_h1 = soup.new_tag("h1", **{'class': 'article-title invisible'})
    new_h1.string = "Title"
    
    new_p = soup.new_tag("p", **{'class': 'article-summary invisible'})
    new_p.string = "Summary"

    new_div.append(new_h1)
    new_div.append(new_p)

    #move all existing content into the new div
    content_to_wrap = list(soup.contents)
    for element in content_to_wrap:
        new_div.append(element)
    
    #replace the original ontents with just the new div
    soup.clear()
    soup.append(new_div)

    return str(soup.prettify())