import xml.etree.cElementTree as ET

OSM_FILE = "Denver.osm"  #Original OSM file (large)
SAMPLE_FILE = "MiniDenver.osm" #Smaller OSM file used throughout the project

k = 20 # Parameter: take every k-th top level element

#Creating the sample file to be used throughout the project
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag

    Reference:
    http://stackoverflow.com/questions/3095434/inserting-newlines-in-xml-file-generated-via-xml-etree-elementtree-in-python
    """
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


with open(SAMPLE_FILE, 'wb') as output:
    output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    output.write('<osm>\n  ')

    # Write every kth top level element
    for i, element in enumerate(get_element(OSM_FILE)):
        if i % k == 0:
            output.write(ET.tostring(element, encoding='utf-8'))

    output.write('</osm>')
    
    
#This function seperates tags into their different catagories to get a count for each
def find_tags(filename):

    tree = ET.parse(filename)
    root = tree.getroot()


    tags = {}
    for child in root:
        tag = child.tag
        if not tag in tags:
            tags[tag] = 1
        else:
            tags[tag] += 1
        
    for way in root.findall('./way/'):
        tag = way.tag
        if not tag in tags:
            tags[tag] = 1
        else:
            tags[tag] += 1
        
    for way in root.findall('./relation/'):
        tag = way.tag
        if not tag in tags:
            tags[tag] = 1
        else:
            tags[tag] += 1
        
    super_tag = root.tag
    if not super_tag in tags:
        tags[super_tag] = 1
    else:
        tags[super_tag] += 1
            
    return tags
    
    
filename = 'MiniDenver.osm'
find_tags(filename)

import re

#This cell matches values to patterns determining validity.
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

#Checking to see if we have any values with problematic characters
def key_type(element, keys):
    if element.tag == "tag":
        if lower.match(element.attrib['k']) is not None:
            keys['lower'] += 1
        elif lower_colon.search(element.attrib['k']) is not None:
            keys['lower_colon'] += 1    
        elif problemchars.search(element.attrib['k']) is not None:
            keys['problemchars'] += 1
        else:
            keys['other'] += 1
        pass
        
    return keys

keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
for _, element in ET.iterparse(filename):
    keys = key_type(element, keys)
    
print (keys)


from collections import defaultdict

#Seperates expected values from unexpected values, returns a dictionary containing values we may need to correct
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_types = defaultdict(set)

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Center", "Circle", "Plaza",
            "Place", "Road", "Way", "Walk", "Trail", "Terrace", "Parkway", "Lane", "Parkway"]

def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

def is_street(elem):
    return (elem.attrib['k'] == "addr:street")

def audit_streets(filename):
    osm_file = open(filename, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(filename, events=("start",)):
        if elem.tag == "way" or elem.tag == "node":
            for tag in elem.iter("tag"):
                if is_street(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types
            
audit_streets(filename)