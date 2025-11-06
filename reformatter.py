from bs4 import BeautifulSoup, NavigableString, Tag
import re
import os

def reformat_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    unwanted_words=['<h3','FORMLABS CUSTOMER SUPPORT GUIDES']
    

    soup = transform_overview_to_strong(soup)
    soup=bolden_estimated_time(soup)
    soup=transform_preceding_p_to_h2(soup)
    soup = transform_required_supplies_table(soup)
    soup=transform_required_supplies_to_grid(soup)

    soup=transform_step_text_to_h3(soup)
    soup=update_alt_text(soup) #must come after converting steps to h3

    soup=transform_kb_required_div(soup)
    
    soup=transform_warning_tables(soup)
    soup=transform_p_to_warning_div(soup)
    soup=transform_warning_h3_to_div(soup)
    soup=transform_note_tables(soup)
    soup=transform_tip_or_note_p_to_div(soup)
    soip=transform_table_with_img_tip(soup)
    
    soup=remove_unnecessary_text(soup, unwanted_words)
    soup=capitalize_specific_words(soup)

    return str(soup.prettify())



def transform_required_supplies_table(soup):
    """converts block of texts into required supplies div if p tag of 'required supplies' exist"""
    required_supplies_p = soup.find('p', string=re.compile(r'Required Supplies:?', re.IGNORECASE))
    
    if not required_supplies_p:
        return soup

    target_table = required_supplies_p.find_parent('table')
    if not target_table:
        return soup

    cells = target_table.find_all('td')
    if len(cells) < 2:
        return soup

    text_cell = cells[0]
    image_cell = cells[1]

    if required_supplies_p:
        h3_tag = soup.new_tag('h3')
        h3_tag.string = required_supplies_p.get_text(strip=True)
        required_supplies_p.replace_with(h3_tag)
    #new tags to add
    new_div_grid = soup.new_tag('div', **{'class': 'slds-grid slds-gutters slds-wrap'})
    new_div_col1 = soup.new_tag('div', **{'class': 'slds-col slds-size_1-of-1 slds-medium-size_1-of-2'})
    new_div_kb_required = soup.new_tag('div', **{'class': 'kb-required'})
    new_div_col2 = soup.new_tag('div', **{'class': 'slds-col slds-size_1-of-1 slds-medium-size_1-of-2'})

    for child in list(text_cell.children):
        new_div_kb_required.append(child)

    img_tag = image_cell.find('img')
    if img_tag:
        new_div_col2.append(img_tag)
    
    new_div_col1.append(new_div_kb_required)
    new_div_grid.append(new_div_col1)
    new_div_grid.append(new_div_col2)

    target_table.replace_with(new_div_grid)

    return soup


def transform_kb_required_div(soup):
    """
    correctly formats the required supplies div if it isnt already
    """
    containers = soup.select('div[class*="slds-grid"]')

    for container in containers:
        #if the columns r already correct skip
        columns = container.find_all('div', class_=lambda c: c and 'slds-col' in c)
        if len(columns) != 2:
            continue

        left_column, right_column = columns[0], columns[1]

        #find the kb-required div in the left column
        kb_required_div = left_column.find('div', class_='kb-required')
        if not kb_required_div:
            #goes onto the next containter
            continue

        #checks if its alr in the right structure(image in right, text in left)
        is_correctly_formatted = (
            right_column.find('img') and
            kb_required_div
        )
        if is_correctly_formatted:
            continue #skip if already right

        img_tag = kb_required_div.find('img')
        estimated_time_p = kb_required_div.find('p', string=lambda s: 'Estimated time:' in s)

        if img_tag:
            #create right column if it doesnt exist already
            new_right_column = soup.new_tag('div', **{'class': 'slds-col slds-size_1-of-1 slds-medium-size_1-of-2'})
            
            #moves the img
            new_right_column.append(img_tag.extract())
            
            #insert the new column
            left_column.insert_after(new_right_column)
        
        #attempt to move the "estimated time" outside of the div
        if estimated_time_p:
            container.insert_after(estimated_time_p.extract())
    return soup


def transform_note_tables(soup):
    """
    converts structure that contains a 'note' or 'tip' into to a <div class="tip"> structure."""
    for table in soup.find_all('table'):
        
        all_p_tags = table.find_all('p', recursive=True)
        if len(all_p_tags) < 2:
            continue
            
        #check nonempty tags
        first_p = all_p_tags[0]
        keyword_match = re.match(r'^(NOTE|TIP)$', first_p.get_text(strip=True), re.IGNORECASE)

        if keyword_match:
            #find heading texts
            keyword = keyword_match.group(1).capitalize() + ':'
            
            #get the body content from the second paragraph
            second_p = all_p_tags[1] 
            body = second_p.get_text(strip=True)
            
            #Create the new <div class="tip"> structure
            new_div = soup.new_tag('div', **{'class': 'tip'})
            
            #Create <h3> for the heading
            h3_tag = soup.new_tag('h3')
            h3_tag.string = keyword
            new_div.append(h3_tag)
            
            #Create <p> for the body
            p_tag_new = soup.new_tag('p')
            p_tag_new.string = body
            new_div.append(p_tag_new)
            
            #Replace the old table with the new div
            table.replace_with(new_div)
            
    return soup


def transform_preceding_p_to_h2(soup):
    """
    Finds and converts the first non-empty tag preceding the Overview section into an h2
    """
    #finds p tag that contains the "Overview" text.
    overview_p_tag = soup.find('p', string=re.compile(r'Overview:', re.IGNORECASE))
    
    if overview_p_tag:
        #find all preceding tags, from closest to furthest.
        preceding_elements = overview_p_tag.find_all_previous(True)
        
        #for every element check if there is a element existing before
        for tag in preceding_elements:
            #get text
            if tag.get_text(strip=True) and tag.name not in ['br', 'img', 'hr']:
                new_h2 = soup.new_tag("h2", **{'class': 'kb-anchor'})
                
                #move the text from the old tag to the new <h2>.
                new_h2.string = tag.get_text(strip=True)
                
                #replace the old tag with the new <h2>.
                tag.replace_with(new_h2)
                
                #stop searching since we found the tag
                break
            
    return soup



def transform_step_text_to_h3(soup):
    """
    Converts 'p' 'h1' 'h2' to proper h3 tags (Step:1/2/3)
    """
    # Match the text to steps (STEP followed by one or more digits, then a colon)
    step_pattern = re.compile(r'STEP\s+(\d+)\s*:\s*(.*)', re.IGNORECASE | re.DOTALL)
    
    step_tags = soup.find_all(['p', 'h1', 'h2','h3'])
    
    for tag in step_tags:
        #collapse internal white space
        full_text = ' '.join(tag.get_text(strip=True).split())
        
        match = step_pattern.match(full_text)
        
        if match:
            step_number = match.group(1).strip()
            raw_title = match.group(2).strip()
            
            if raw_title:
                formatted_title = raw_title.lower().capitalize()
            else:
                formatted_title = ""

            new_h3_text = f"Step {step_number}: {formatted_title}"
            
            new_h3 = soup.new_tag('h3')
            new_h3.string = new_h3_text
            
            tag.replace_with(new_h3)

    return soup


def update_alt_text(soup):
    images = soup.find_all('img')
    # container to keep count of img
    image_counts = {}

    for img in images:
        prev_h3 = img.find_previous('h3')

        if prev_h3:
            #gets content of h3 and acts as the reference key
            h3_key = prev_h3.get_text().strip()

            #image counting logic
            if h3_key not in image_counts:
                image_counts[h3_key] = 1
            else:
                image_counts[h3_key] += 1
            current_img_number = image_counts[h3_key]

            #src renaming logic --> strip "step" replace whitespace with "-" and lowercase it
            text_without_step = re.sub(r'^Step \d+:\s*', '', h3_key, flags=re.IGNORECASE).strip()
            #remove commas
            text_without_punc = re.sub(r'[,:]', '', text_without_step)

            alt_with_dashes = re.sub(r'\s+', '-', text_without_punc)
            base_imgfile = alt_with_dashes.lower()

            # attach the # of img if there is more than 1
            if current_img_number > 1:
                final_filename_base = f"{base_imgfile}-{current_img_number}"
            else:
                final_filename_base = base_imgfile

            # find src filepath
            original_src = img.get('src', '')
            
            # reads the current file path
            src_parts_match = re.match(r'^(.*[/])?(.*)(\.[a-zA-Z0-9]+)$', original_src)
            
            path_prefix = src_parts_match.group(1) if src_parts_match and src_parts_match.group(1) else ''
            extension = src_parts_match.group(3).lower() if src_parts_match and src_parts_match.group(3) else '.png'
            
            #get the existing filename
            old_filename = src_parts_match.group(2) + src_parts_match.group(3) if src_parts_match else original_src
            
            #makes new src file path (for HTML)
            new_src_value = f"{path_prefix}{final_filename_base}{extension}"
            
            #define the new physical filename
            new_filename = f"{final_filename_base}{extension}"

            #actual file renaming
            old_filepath = os.path.join(os.getcwd(), old_filename)
            new_filepath = os.path.join(os.getcwd(), new_filename)
            
            #Only attempt to rename if the old file exists and the names are different.
            if os.path.exists(old_filepath) and old_filename != new_filename:
                try:
                    os.rename(old_filepath, new_filepath)
                    # print(f"Successfully renamed physical file: {old_filename} -> {new_filename}") # Debug
                except Exception as e:
                    print(f"Error renaming physical file {old_filename}: {e}")
            
            img['src'] = new_src_value
            img['alt'] = h3_key
            img['title'] = h3_key
           
    return soup

def transform_overview_to_strong(soup):
    #pattern to match overview
    overview_pattern = re.compile(r'(OVERVIEW\s*?:)', re.IGNORECASE)
    
    #iterate all text string
    for text_node in soup.find_all(string=True):
        #if string is in p
        if text_node.parent and text_node.parent.name == 'p':
            original_text = text_node.string
            
            if overview_pattern.search(original_text):
                parts = overview_pattern.split(original_text, maxsplit=1)
                
                new_elements = []
                
                #append text before the match @index 0
                if parts[0]:
                    new_elements.append(parts[0])

                #add strong tag
                if len(parts) > 1: #make sure match was found
                    strong_tag = soup.new_tag('strong')
                    strong_tag.string = "Overview:" 
                    new_elements.append(strong_tag)
                #also append after the match
                if len(parts) > 2 and parts[2]:
                    new_elements.append(parts[2])

                #replace old text with new
                text_node.replace_with(*new_elements)
                
    return soup


def transform_workspace_p_to_h2(soup): 
    p_tag = soup.find('p', string=re.compile(r'Preparing the workspace', re.IGNORECASE))
    
    if p_tag:
        new_h2 = soup.new_tag("h2", **{'class': 'kb-anchor'})
        new_h2.string = p_tag.get_text(strip=True)
        p_tag.replace_with(new_h2)
        
    return soup


def transform_p_to_warning_div(soup):
    """
    Finds and converts paragraphs starting with NOTICE, DANGER, or CAUTION into a warning div
    """
    #finds <p> tags that says notice
    p_tags = soup.find_all('p')
    for p_tag in p_tags:
        #check if the text starts with 'NOTICE:'
        if p_tag.get_text().strip().startswith('NOTICE:'):
            # Split the text into the heading and the body
            parts = p_tag.get_text().strip().split(':', 1)
            if len(parts) == 2:
                heading_text = parts[0].strip() + ':'
                body_text = parts[1].strip()

                #create the new warning div class
                new_div = soup.new_tag('div', **{'class': 'warning'})

                #make h3 tag
                h3_tag = soup.new_tag('h3')
                h3_tag.string = heading_text

                #make p tag for body
                new_p = soup.new_tag('p')
                new_p.string = body_text

                #combine
                new_div.append(h3_tag)
                new_div.append(new_p)
                p_tag.replace_with(new_div)
            
    return soup


def transform_tip_or_note_p_to_div(soup):
    """
    format tips/notes properly by searching regex tip/notes
    """
    #regex to find 'Tip:' or 'Note:' at the start of the string, case-insensitive
    pattern = re.compile(r'^(Tip:|Note:)\s*', re.IGNORECASE)
    
    p_tags = soup.find_all('p')
    
    for p_tag in p_tags:
        #check if text match the pattern
        p_text = p_tag.get_text().strip()
        match = pattern.match(p_text)
        
        if match:
            #get the original heading
            original_heading = match.group(1).capitalize()

            #get remaining content
            content = p_text[match.end():].strip()

            #make new div
            new_div = soup.new_tag('div', **{'class': 'tip'})
            
            #make h3, p tags
            new_h3 = soup.new_tag('h3')
            new_h3.string = original_heading
            
            new_p = soup.new_tag('p')
            new_p.string = content
            
            new_div.append(new_h3)
            new_div.append(new_p)
            
            p_tag.replace_with(new_div)

    return soup


def transform_warning_h3_to_div(soup):
    """
    Finds h3 tags with specific warning text and wraps them and the
    immediately following p tag in a new div with class 'warning'
    """
    warning_keywords = ['NOTICE:', 'WARNING:', 'DANGER:', 'CAUTION:']
    h3_tags = soup.find_all('h3')

    for h3_tag in h3_tags:
        #check if the h3 tag's parent is already a 'div' with the 'warning' class.
        if h3_tag.parent and h3_tag.parent.name == 'div' and 'warning' in h3_tag.parent.get('class', []):
            continue  #skips since its alr correct

        h3_text = h3_tag.get_text(strip=True).upper()
        
        is_warning_heading = False
        for keyword in warning_keywords:
            if h3_text.startswith(keyword):
                is_warning_heading = True
                break
                
        if is_warning_heading:
            #finds the next sibling tag ('p' usually)
            next_p = h3_tag.find_next_sibling('p')

            if next_p:
                new_div = soup.new_tag('div', **{'class': 'warning'})

                #insert new div before the h3 tag
                h3_tag.insert_before(new_div)

                new_div.append(h3_tag.extract())  #move the h3 and p tags into the new div
                new_div.append(next_p.extract()) 

    return soup 



def transform_warning_tables(soup):

    for table in soup.find_all('table'):
            p_tag = table.find('p', recursive=True)
            ul_tag = table.find('ul', recursive=True)
            
            #check for a table that contains a warning and a bullet list
            if p_tag and ul_tag:
                text = p_tag.get_text(strip=True)
                parts = text.split(':', 1)
                
                if len(parts) > 0 and parts[0].strip().upper() in ['CAUTION', 'DANGER', 'WARNING', 'NOTICE']:
                    heading = parts[0].strip().capitalize() + ':'
                    
                    new_div = soup.new_tag('div', **{'class': 'warning'})
                    h3_tag = soup.new_tag('h3')
                    h3_tag.string = heading
                    new_div.append(h3_tag)
                    
                    new_div.append(ul_tag)  #append the ul tag to the new div
                    
                    table.replace_with(new_div) #replace the whole thing with the new div

            #else if 
            elif p_tag:
                text = p_tag.get_text(strip=True)
                parts = text.split(':', 1)
                
                if len(parts) > 1 and parts[0].strip().upper() in ['CAUTION', 'DANGER', 'WARNING', 'NOTICE']:
                    heading = parts[0].strip().capitalize() + ':'
                    body = parts[1].strip()
            
                    new_div = soup.new_tag('div', **{'class': 'warning'})
                    h3_tag = soup.new_tag('h3')
                    h3_tag.string = heading
                    new_p = soup.new_tag('p')
                    new_p.string = body
                    new_div.append(h3_tag)
                    new_div.append(new_p)
                    table.replace_with(new_div)
            
                
    return soup


def transform_preceding_p_to_h2(soup):
    """
    converts the preceding element of overview into h2, and add anchor (basically the headers)
    """
    #look for overview tag
    overview_tags = soup.find_all(lambda tag: tag.name in ['p'] and tag.strong and tag.strong.string and 'Overview:' in tag.strong.string)
  
    for overview_p_tag in overview_tags:
        preceding_element = overview_p_tag.find_previous(lambda tag: tag.get_text(strip=True) and tag.name not in ['h2','br', 'img', 'hr', 'style'])
        
        if preceding_element:
            #get the content to put it in h2
            heading_text = preceding_element.get_text(strip=True)
            #format the anchor name w dashes and lower case
            anchor_name_dashes = re.sub(r'\s+', '-', heading_text)
            final_anchor_name = anchor_name_dashes.lower()
            
            #make new h2 tag
            new_h2 = soup.new_tag("h2", **{'class': 'kb-anchor'})
            new_h2.string = heading_text
            
            #create new a tag and passes the name attribute value
            new_anchor = soup.new_tag("a", attrs={'name': final_anchor_name, 'class': 'kb-anchor'})
            
            #put anchor and h2 before the old stuff
            preceding_element.insert_before(new_anchor)
            preceding_element.insert_before(new_h2)
            
            #remove old stuff
            preceding_element.decompose()
            
            #h2 comes after the new anchor
            inserted_h2 = new_anchor.find_next_sibling('h2')

            if inserted_h2 and new_anchor.next_sibling != inserted_h2:
                 inserted_h2.insert_before(new_anchor.extract())
            
    return soup



def transform_required_supplies_to_grid(soup):
    """
    Finds the <h3>Required Supplies:</h3> tag and the sequential P, UL, and
    IMG elements that follow it, wrapping them into the two-column grid structure. skips if h3 alr exist inside target structure
    """
    h3_tags = soup.find_all('h3', string=re.compile(r'Required Supplies\s*:', re.IGNORECASE))
    
    for h3_tag in h3_tags:
        #check if the H3 is ALREADY inside a target slds-grid (the skip condition)
        if h3_tag.find_parent('div', class_='slds-grid'):
            continue
            
        elements_to_wrap = [h3_tag] #define the boundary
        img_tag = None
        
        #collect all siblings
        current_sibling = h3_tag.next_sibling
        while current_sibling:
            if isinstance(current_sibling, NavigableString) and current_sibling.strip() == "":
                current_sibling = current_sibling.next_sibling
                continue
            
            #stop collectnig when we hit the images
            if current_sibling.name == 'img':
                img_tag = current_sibling
                break
                
            #only collect p and list for the text column
            if current_sibling.name in ['p', 'ul', 'ol']:
                elements_to_wrap.append(current_sibling)
            
            elif current_sibling.name in ['h2', 'h3', 'h4']: #stop if we hit another heading
                break
            
            current_sibling = current_sibling.next_sibling

        if not img_tag:
            continue
            
        #Create the target HTML structure
        
        new_div_grid = soup.new_tag('div', **{'class': 'slds-grid slds-gutters slds-wrap'})
        
        #left column=texts
        new_div_col1 = soup.new_tag('div', **{'class': 'slds-col slds-size_1-of-1 slds-medium-size_1-of-2'})
        new_div_kb_required = soup.new_tag('div', **{'class': 'kb-required'}) # Inner wrapper
        new_div_col1.append(new_div_kb_required)
        
        #img for right column
        new_div_col2 = soup.new_tag('div', **{'class': 'slds-col slds-size_1-of-1 slds-medium-size_1-of-2'})
        
        #Move/Append the elements
        h3_tag.insert_before(new_div_grid)
        
        #combine all text on the left side of column
        for element in elements_to_wrap:
            new_div_kb_required.append(element.extract()) #extract to remove the original location
            
        new_div_col2.append(img_tag.extract()) 
        new_div_grid.append(new_div_col1)
        new_div_grid.append(new_div_col2)

    return soup



#simple methods down here
def remove_unnecessary_text(soup, unwanted_strings):
    """
    Finds and removes unwanted strings from all texts --> removing typos mostly
    """
    # Create a regex pattern to find all unwanted strings at once
    pattern = re.compile('|'.join(re.escape(s) for s in unwanted_strings), re.IGNORECASE)

    #iterates through all the text node
    for text_node in soup.find_all(string=True):
        #avoid text inside script or style tags
        if text_node.parent.name in ['script', 'style']:
            continue
        
        #change the unwanted texts
        original_text = text_node.string
        new_text = pattern.sub('', original_text)
        if new_text != original_text:
            text_node.replace_with(NavigableString(new_text))

    return soup

def capitalize_specific_words(soup):
    words_to_capitalize = {
        'backlight unit': 'Backlight Unit',
        'wi-fi': 'Wi-Fi',
        "wifi": 'Wi-Fi',
        'lpu': 'LPU',
        'rfid': 'RFID',
        'light processing unit': 'Light Processing Unit',
        'led': 'LED',
        'backlight unit': 'Backlight Unit',
        'hdmi':"HDMI",
        "som": "SOM",
        "x-axis": "X-axis",
        "y-axis": "Y-axis",
        "z-axis": "Z-axis",
        "usb": "USB",
        "vhb": "VHB",
        "finish kit": "Finish Kit",
        "finishing tools":"Finishing Tools",
        "levelsense": "LevelSense"
    }
     #iterate over all text nodes
    for text_node in soup.find_all(string=True):
        if text_node.parent.name in ['script', 'style']:
            continue

        original_text = text_node.string
        new_text = original_text
        for lowercase_word, capitalized_word in words_to_capitalize.items():
            new_text = re.sub(r'\b' + re.escape(lowercase_word) + r'\b', capitalized_word, new_text, flags=re.IGNORECASE)
        
        if new_text != original_text:
            text_node.replace_with(NavigableString(new_text))

    return soup

def bolden_estimated_time(soup):
    for text_node in soup.find_all(string=True):
        if 'Estimated time' or 'Estimated time:'in text_node:
            text_content=text_node.string
            bolden_text=soup.new_tag('strong')
            bolden_text.string='Estimated time:'
            new_text=text_content.replace('Estimated time:', str(bolden_text),1)

            new_elements=BeautifulSoup(new_text, 'html.parser').contents
            text_node.replace_with(*new_elements)
    return soup

def transform_table_with_img_tip(soup):
    """
    formats tip and image table properly
    """
    tip_divs = soup.find_all('div', class_='tip')
    
    for tip_div in tip_divs:
        #check the immediate next sibling after the tip div
        next_sibling = tip_div.next_sibling
        
        # Skip NavigableStrings that are only whitespace
        while isinstance(next_sibling, NavigableString) and next_sibling.strip() == "":
            next_sibling = next_sibling.next_sibling

        #checks if the next element is a <p> tag
        if next_sibling and next_sibling.name == 'p':
            p_tag_to_move = next_sibling
            
            #moves the entire <p> tag inside the <div class="tip">
            tip_div.append(p_tag_to_move.extract())

    return soup



