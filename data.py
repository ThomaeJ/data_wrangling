import schema
import csv
import codecs
import cerberus

mapping =  {"Ct": "Court", "Ln": "Lane", "Hampden Ave": "Hampden Avenue"}

#This function replaces bad values with values we can use
def fixer(name, mapping):
    
    for k, v in mapping.iteritems():
        if k in name:
            name = name.replace(k, v)
    return name

OSM_PATH = "MiniDenver.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']

def shape_element(element):
    """Clean and shape node or way XML element to Python dict"""
    
    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        for item in NODE_FIELDS:
            node_attribs[item] = element.get(item)
        for child in element:
            tag_dict = {}
            colon = child.get('k').find(':')
            if (child.tag == 'tag'):
                tag_dict['id'] = element.get('id')
                #call to the fixer function for name updating
                tag_dict['value'] = fixer(child.get('v'), mapping)
                if (colon != -1):
                    type_value = child.get('k')[:colon]
                    key_value = child.get('k')[colon+1:]
                    tag_dict['type'] = type_value
                    tag_dict['key'] = key_value
                else:
                    tag_dict['key'] = child.get('k')
                    tag_dict['type'] = 'regular'
                tags.append(tag_dict)
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        for item in WAY_FIELDS:
            way_attribs[item] = element.get(item)
        n = 0
        for child in element:
            if child.tag == 'nd':
                nd_dict = {}
                nd_dict['id'] = element.get('id')
                nd_dict['node_id'] = child.get('ref')
                nd_dict['position'] = n
                n += 1
                way_nodes.append(nd_dict)
            if child.tag == 'tag':
                colon = child.get('k').find(':')
                wtag_dict = {}
                wtag_dict['id'] = element.get('id')
                wtag_dict['value'] = fixer(child.get('v'), mapping)
                if (colon != -1):
                    type_value = child.get('k')[:colon]
                    key_value = child.get('k')[colon+1:]
                    wtag_dict['type'] = type_value
                    wtag_dict['key'] = key_value
                else:
                    if child.get('k') == 'upload_uuid':
                        wtag_dict['key'] = 'NULL'
                    else:
                        wtag_dict['key'] = child.get('k')
                        wtag_dict['type'] = 'regular'
                    tags.append(wtag_dict)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)
                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])



if __name__ == '__main__':
    process_map(OSM_PATH, validate=False)
