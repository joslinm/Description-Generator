#!/usr/bin/env python

from xml.dom import minidom 
import urllib2, gzip, cStringIO, os, sys

query_types = {
    'all':1,
    'artist':1,
    'release':1,
    'label':1, }

def try_to_prompt(prompt_text):
    '''
    Prompt the user for input. 
    If EOF is found, then the program will exit.
    '''
    try:
        return raw_input(prompt_text)
    except EOFError:
        print
        exit(0)

def http_query(base, args):
    '''
    Construct an HTTP query with a base url and a dict of arguments.
    '''
    url = base
    arg_names = args.keys()
    if len(arg_names) > 0:
        url += '?'
        arg_strings = [''.join((x,'=',args[x])) for x in arg_names]
        url += '&'.join(arg_strings)
    return url

api = ''
concat = '+'        #used to implode a string below
search_string = '99'
search_type = 'all'
i_search = None;    #Internal search if needed
reflist = None      
uri = None

#User switches
summary = 0
exact = 0


def initialize(): 
    global api
    if(os.path.exists('settings.txt')):
        f = open('settings.txt', 'r')
        api = f.readline()
        api = str.split(api, ':')[1].strip()
    else :
        default_settings = (
            'API KEY :<Please Insert Yours Here>',
            "// You can comment on new lines using '//'",
            "// You can not begin a comment in the middle of a line.",
            "// The list of tags is as so :",
            "// Album Title...  %t",
            "// Artist Name...  %a",
            "// Labels...       %x",
            "// Catnos...       %n",
            "// Format(s)...    %f",
            "// Country...      %c",
            "// Released...     %r",
            "// Track Listing...%l",
            "// Genre(s)...     %g",
            "// Style(s)...     %s",
            "// --*I'll get you started with a template*--", "",
            "[b]%t[/b]",
            "by %a",
            "%r", "",
            "%l", "",
            "Country: %c || Genre: %g || Label: %x", "")

        f = open('settings.txt', 'w')

        f.write("\n".join(default_settings))

        print("**This is your first time running the script")
        print("**Please fill out the settings.txt API key and restart")
        sys.exit()

def disc_request(url):
    print url;
    url = url.strip('+')

    # Form the http request.
    request = urllib2.Request(url)
    request.add_header('Accept-Encoding', 'gzip')  

    # Send the request.
    response = urllib2.urlopen(request)  

    # Read the reply.
    data = response.read() 

    # Extract the response.
    try:
        data_stream = cStringIO.StringIO(data)
        zipped_data = gzip.GzipFile(fileobj = data_stream)
        unzipped_data = zipped_data.read()
    except:
        unzipped_data = data

    # Parse the response as xml, and return the results.
    xmldoc = minidom.parseString(unzipped_data)
    return xmldoc
    

def search_menu(reflist, iterator):
    '''
    Let the user browse a list of search results.
    '''

    # Initialize state variables.
    input_ = '-1'
    counter = 0
    filter_ = None

    # Output one page of results at a time.
    while(input_ == '-1'):

        # Filter results containing a substring filter_.
        if(filter_ is not None):
            innercounter = 0
            newlist = [-1]
            filter_ = filter_.lower()
            
            print filter_

            # Loop over the whole list of results.
            for x in reflist:
                x.toxml()
                node = x.getElementsByTagName(iterator)
                title = node[0].firstChild.data
                title = title.lower()
                success = (title).find(filter_)
                
                # Add the result if it matches the filter.
                if(success > -1): newlist[0:0] = [reflist.index(x)]
                    
                #print title + " == " + str(success)
                #raw_input('success = ' + str(success))
            
            newlist.remove(-1)
            newlist.reverse()
            
            # Move matches to the beginning of the search results.
            for i in newlist:
                #print i
                try:
                    match = reflist[i]
                    reflist[i:i+1] = []
                    reflist[0:0] = [match]
                except: pass

            # Reset the counter to the beginning of the matches.
            counter = 0

        # Set the default response.
        default = counter

        # Print the next page.
        for x in reflist[counter:counter+9]:
            node_name = x.nodeName
            if(node_name == 'result'):
                rtype = x.attributes['type'].value
                if(summary and rtype == 'release'):
                    y = x
                    y.toxml()
                    s_node = y.getElementsByTagName('summary')
                    s_msg = s_node[0].firstChild.data
            elif(node_name == 'artist'):
                rtype = 'artist'
            elif(node_name == 'release'):
                rtype = 'release'
            
            x.toxml()
            node = x.getElementsByTagName(iterator)

            if(node.length > 0):
                title = node[0].firstChild.data; #data
                print '[' + str(counter) + '] ' + title + ' [' + rtype + '] '
                if(node_name == 'result' and rtype == 'release' and summary):
                    print '>->->Summary' + '-'*40
                    print s_msg
                    print '------------' + '-'*40 + '\n'
                counter += 1
        
        if(counter < reflist.length - 1):
            if(reflist.length > counter + 1):
                print '[-1] See More... (' + str(reflist.length - counter) + ' remaining)'
            elif(x.nodeName == 'result'):
                print 'End Of Search Results'

        input_ = try_to_prompt(
                ''.join((
                    '\n\nOption [', str(default),'] or Filter: ')));
        if(len(input_) == 0):
            input_ = 0
        else:
            try:
                input_ = int(input_)
                if(input_ == -1):
                    input_ = '-1'
            except:
                filter_ = input_
                input_ = '-1'
    return input_

def get_artist_uri(node): 
    uri = node.firstChild.data 
    #Get the url until ? is hit (this avoids complications) 
    new_uri = str.split(str(uri), '?')[0] 
    uri =  new_uri + '?f=xml&api_key=' + api
    return uri 

def pull_release_id_from_user_url(uri):
    uri = uri.strip('+')
    explode = str.split(uri, '/')
    r = explode[len(explode) - 1] #return last element which is the ID
    #print r
    return r
    
def get_release_uri(node):
    uri = node.firstChild.data
    #print "uri : " + uri
    splut = str.split(str(uri), '/')
    counter = 2
    while(splut[counter] != 'release'):
        counter += 1
        _id = splut[counter + 1]
    
    args = {'f':'xml', 'api_key':api}
    url = 'http://www.discogs.com/release/' + _id
    return http_query(url, args)

def get_snippet(node, tag):
    content = ['temporary']

    attr = 'name'
    if tag == 'catno':
        tag = 'label'
        attr = 'catno'

    reflist = node.getElementsByTagName(tag)
    
    if reflist is None: return None

    if(len(reflist) > 0):
        if(tag == 'label' or tag == 'format'): 
            # Info is in attributes.
            for x in reflist:
                title = x.attributes[attr].value
                #print tag + " Name: " + title
                content.append(title)
        elif(tag == 'artist'):
            for x in reflist:
                if(x.parentNode.nodeName != 'extraartists'):
                    title = x.firstChild.firstChild.data
                    #print tag + " Name: " + title
                    content.append(title)
        elif(tag == 'title'): 
            # Only get the first title
            title = reflist[0].firstChild.data
            #print tag + " Name: " + title
            content.append(title)
        else:
            for x in reflist:
                title = x.firstChild.data
                #print tag + " Name: " + title
                content.append(title)

    # Remove initial declaration.
    content[0:1] = []
    return content

def get_data_of_first_child_for_tag(node, tag):
    '''
    Return the data from the first child of the first element of node
    with the given tag.
    '''
    # Get all the track number.
    reflist = node.getElementsByTagName(tag)

    if len(reflist) <= 0: return ''

    element = reflist[0]

    if element.firstChild is None: return ''

    # Attempt to extract the position from the node.
    try: return reflist[0].firstChild.data
    except Exception: return ''

def get_track_list(node):
    content = [['position', 'title', 'duration']]

    # Get all track xml elements.
    reflist = node.getElementsByTagName('track')
    skip = 0

    # If there is at least one track in the reflist.
    if(len(reflist) > 0):

        # Iterate over tracks.
        for x in reflist: 
            x.toxml()
            
            position = get_data_of_first_child_for_tag(x,'position')
                
            # Get the track title.
            title = get_data_of_first_child_for_tag(x, 'title')
                
            # Get the track duration.
            duration = get_data_of_first_child_for_tag(x, 'duration')
            
            # Skip the track if there was an error or something.
            if(skip == 1): 
                skip = 0
                continue

            # Append the track information to the tracklist.
            content.append([[position, title, duration]])

    # Remove initial declaration via a splice.
    content[0:1] = []

    # Return the tracklist.
    return content

def build_release(data):
    '''
    Creates a string description of a release described by 'data'. Uses
    the template found in settings.txt
    '''
    #First get the artist(s)
    node = data[0]
    node.toxml()
    title = get_snippet(node, 'title')
    artists = get_snippet(node, 'artist')
    labels = get_snippet(node, 'label')
    catnos = get_snippet(node, 'catno')
    formats = get_snippet(node, 'format')
    genres = get_snippet(node, 'genre')
    styles = get_snippet(node, 'style')
    country = get_snippet(node, 'country')
    released = get_snippet(node, 'released')
    tracks = get_track_list(node)
    
    f = open("settings.txt", 'r')
    
    template = f.readlines()
    variable = 0
    output = ''
    # Process each template line
    for l in template:
        #If a comment or API do nothing
        if(l.startswith('//') or l.find('API') != -1): 
             continue
        else:
            # Iterate over characters in the line.
            for a in l:
                if(variable):
                    # Print release title.
                    if(a == 't'):
                        output += title[0]
                        
                    # Print artists.
                    elif(a == 'a'):
                        innercounter = len(artists)
                        for x in artists: 
                            if(x == 'Various'):
                                output += x + ' Artists including...\n'
                                innercounter -= 1
                            else:
                                output += x
                                innercounter -= 1
                                if(innercounter > 0):
                                    output += ' , ' 
                    # Print labels.
                    elif(a == 'x'):
                        innercounter = len(labels)
                        for x in labels: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '
                    # Print release formats.
                    elif(a == 'f'):
                        innercounter = len(formats)
                        for x in formats: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '

                    # Print release country
                    elif(a == 'c'):
                        innercounter = len(country)
                        for x in country: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '

                    # Print year released.
                    elif(a == 'r'):
                        innercounter = len(released)
                        for x in released: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '

                    # Print tracklist.
                    elif(a == 'l'):
                        innercounter = len(tracks)
                        for x in tracks:
                            if(x[0][0] != ''):
                                output += x[0][0] + '.) '
                            if(x[0][1] != ''):
                                output += x[0][1]
                            if(x[0][2] != ''):
                                output += ' ['+x[0][2]+']\n'
                            if(not output.endswith('\n')):
                                output += '\n'

                    # Print genres.
                    elif(a == 'g'):
                        innercounter = len(genres)
                        for x in genres: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ', '
                    elif(a == 's'):
                        innercounter = len(styles)
                        for x in styles:
                            output += x
                            innercounter -=1
                            if innercounter > 0:
                                output += ', '
                    elif(a == 'n'):
                        innercounter = len(catnos)
                        for x in catnos:
                            output += x
                            innercounter -=1
                            if innercounter > 0:
                                output += ', '
                    variable = 0
                # If the last character read was not '%'
                else: 
                    # Reading the beginning of a variable substitution.
                    if(a == '%'): variable = 1
                    # Reading a normal character.
                    else: output += a

    # Print the release description.
    print output

    # Prompt to save description as text file.
    print 'Options: '
    print '[0] Save to file ' + title[0] + '.txt'
    print '[1] Do nothing\n\n'

    # Read user response.
    sel = try_to_prompt( 'Selection [0] : ' )

    # Save if requested.
    if(len(sel) == 0 or sel == 0):
        f = open(title[0] + '.txt', 'w')
        f.write(output.encode('latin-1'))
        f.flush()
        f.close()

#################
# MAIN FUNCTION #
#################

# Process any command line arguments
if(len(sys.argv) > 1):
    for x in sys.argv:
        # I don't really know what this paragraph is for.
        if(x[0] != '-'):
            if(search_type == 'release'):
                try: i_search  = int(x)
                except (TypeError, ValueError):
                    print "**You cannot search releases."
                    print "**Search normally or use the release ID#."
                    search_type = 'all'
            i_search = x

        # Check summary printing option.
        elif(x == '-s'):
            summary = 1

        # Check exact query matching option.
        elif(x == '-exact'):
            exact = 1

        # Check release url specification.
        elif(x == '-url'):
            if(len(i_search) >= 0):
                    i_search = pull_release_id_from_user_url(i_search)
                    search_type = 'release'

        # Check for release search option.
        elif(x == '-release'):
            search_type = 'release'

        # Check for label search option.
        if(x == '-label'):
            search_type = 'label'

        # Check for artist search option.
        elif(x == '-artist'):
            search_type = 'artist'

# Read the API key from settings.txt
initialize()        


while(search_string != "-99"): 
    # Do we need the user to specify a URL?
    if(uri == 'set'): uri = try_to_prompt("Enter URL: ")

    # Make sure that the search type is set to something
    if(search_type == None): search_type = 'all'

    # If an internal search is unnecessary, and there is no URL given.
    if(i_search == None and uri == None):
        # Read in a search query.
        search_string = try_to_prompt("Search: ")

        # Split the query into tokens
        explode = str.split(search_string, ' ')

        # Initialize a string for the http query string.
        implode = '' #We'll reconstruct our search query here
        for x in explode:
            if(x == '-release'): search_type = 'release'
            elif(x == '-artist'): search_type = 'artist'
            elif(x == '-label'): search_type = 'label'
            elif(x == '-exact'): exact = 1
            elif(x == '-s'): summary = 1
            elif(x == '-url'): 
                if(len(implode) >= 0):
                    i_search = pull_release_id_from_user_url(implode)
                    search_type = 'release'
            else: implode += x + '+'
        
    # An internal search is required.
    if(i_search is not None):
        print 'inside..'
        search_string = i_search
        
        print search_type

        # If we are searching artists.
        if(search_type == 'artist'):
            print search_string
            # Suggest moving the word "The" to the end of artist names.
            if(search_string.lower().startswith('the')):
                split = str.split(search_string, ' ')
                innercounter = 0
                new_s = ''
                for x in split: 
                    if (innercounter > 0):
                        new_s += x + ' '
                    innercounter += 1
                new_s += ', The'
                print("Did you mean " + new_s + " ?")

        # If we are searching releases.
        if(search_type == 'release'):
            # Make sure the query is a release ID number (integer).
            try:
                int(search_string)
                implode = search_string
            except (TypeError, ValueError):
                print "**You cannot search releases \n**Please use the release ID number in the future"
                search_type = 'all'

        # We are searching all entries.
        else:
            explode = str.split(search_string, ' ')
            implode = concat.join(explode)

    # Break if we are unable to make a query.
    if(search_string == '-99'): break
    
    # Form a URI if we don't already have one.
    if(uri == None):

        discogs_base = 'http://www.discogs.com'
        args_base = {'f':'xml', 'api_key':api}

        if(search_type == 'all'):
            url = discogs_base + '/search'
            args = args_base.copy()
            args['type'] = 'all'
            args['q'] = implode
            uri = http_query(url, args)
        elif(search_type == 'artist'):
            url = '/'.join((discogs_base, 'artist', implode))
            uri = http_query(url, args_base)
        elif(search_type == 'label'): 
            url = '/'.join((discogs_base, 'label', implode))
            uri = http_query(url, args_base)
        elif(search_type == 'release'):
            url = '/'.join((discogs_base, 'release', implode))
            uri = http_query(url, args_base)
    
    # Get the query results.
    xmldoc = disc_request(uri)

    # Get the type of document returned from the query.
    doc_type = xmldoc.firstChild.firstChild.nodeName
    
    # If we are searching all entry types.
    if(search_type == 'all'): 
        # If we are looking for exact matches to the query
        if(exact):
            reflist = xmldoc.getElementsByTagName('exactresults')
            if(reflist < 1): 
                reflist = xmldoc.getElementsByTagName('result')
            node = reflist[0]
            node.toxml()
            # This is the parent node to look in (result)
            reflist = node.getElementsByTagName('result') 

        # If we are looking for any query matches, use all results.
        else:
            reflist = xmldoc.getElementsByTagName('result')
            
        # If the query returned no results
        if(reflist.length < 1):
            print('nothing')
            i_search = None
            uri = None

        # Process results returned from the query.
        else:
            # Tell the function to show a menu using the TITLE as options.
            selected = search_menu(reflist, 'title') 

            # Select the next entry.
            node = reflist[int(selected)]

            # Get the type of the entry.
            rtype = node.attributes['type'].value
            node.toxml()
            # Get URIs attached to the result entry.
            uri_node = node.getElementsByTagName('uri')

            # If the entry is an artist entry.
            if(rtype == 'artist'):
                uri = get_artist_uri(uri_node[0])
                search_type = 'artist'

            # If the entry is a release entry.
            elif(rtype == 'release'):
                uri = get_release_uri(uri_node[0])
                search_type = 'release'

    # We are not searching all entry types.
    # If the query returned a label document.
    elif(doc_type == 'label'):

        # Get the releases from the label.
        reflist = xmldoc.getElementsByTagName('release')

        if(reflist.length < 1):
            print('nothing')
        else:
            # Get the select a title from the list of releases.
            selected = search_menu(reflist, 'title')

            # Get the title of the selected release.
            title = reflist[int(selected)].getElementsByTagName('title')

            # Try to set up an internal search for the title.
            if(len(title) > 0):
                i_search = title
                uri = None
            else:
                print "Can't use this data to process your request"
                i_search = None
                uri = None

    # If the query returned an artist document.
    elif(doc_type == 'artist'):
        # Get a list of the returned artists.
        reflist = xmldoc.getElementsByTagName('artist')
        if(reflist.length < 1):
            print('nothing')
            i_search = None
            uri = None
        elif(reflist.length > 1):
            # Get a selected artist from the list.
            selected = search_menu(reflist, 'name')

            # Handle the selected artist node.
            node = reflist[int(selected)]

            # Get the artist page URI.
            uri = get_artist_uri(uri_node)

            # Retrieve the artist URI.
            xmldoc = disc_request(uri)

            # Select the artist
            reflist = xmldoc.getElementsByTagName('artist')
            node = reflist[0]
        else:
            node = reflist[0]
        
        # Get the artist releases.
        reflist = xmldoc.getElementsByTagName('release')

        # Have the user select a title.
        selection = search_menu(reflist, 'title')

        # Get the release ID number of the chosen release.
        id_ = reflist[int(selected)].attributes['id'].value
        
        print "id: " + id_
        i_search = id_
        search_type = 'release'
        uri = None

    # If the query returned a release document.
    elif(doc_type == 'release'):
        # Get the release node.
        node = xmldoc.getElementsByTagName('release')

        # Build and print the release description.
        build_release(node)

        # Set up for a new search.
        i_search = None
        uri = None
        search_type = 'all'

    # The query returned an unknown document type.
    else:
        print 'Discogs returned an Unknown XML file'
        print doc_type
        doc_type = None
        i_search = None
        uri = Nonertype = x.attributes['type'].value
