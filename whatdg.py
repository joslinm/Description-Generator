#description generator

from xml.dom import minidom 
import urllib2, gzip, cStringIO, os, sys

api = ''
concat = '+'        #used to implode a string below
search = ["99", 'all']  #[0] = query [1] = type
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
        api = str.split(api, ':')[1]
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
    request = urllib2.Request(url)
    request.add_header('Accept-Encoding', 'gzip')  
    response = urllib2.urlopen(request)  
    data = response.read() 
    try:
        unzipped_data = gzip.GzipFile(fileobj = cStringIO.StringIO(data)).read()
    except:
        unzipped_data = data
    xmldoc = minidom.parseString(unzipped_data)
    return xmldoc
    

def search_menu(reflist, iterator):
    input_ = '-1'
    counter = 0
    filter_ = None
    while(input_ == '-1'):
        if(filter_ is not None):
            innercounter = 0
            newlist = [-1]
            filter_ = filter_.lower()
            
            print filter_
            for x in reflist:
                x.toxml()
                node = x.getElementsByTagName(iterator)
                title = node[0].firstChild.data
                title = title.lower()
                success = (title).find(filter_)
                
                if(success > -1): #found
                    newlist.insert(0, reflist.index(x))
                    
                #print title + " == " + str(success)
                #raw_input('success = ' + str(success))
            
            newlist.remove(-1)
            newlist.reverse()
            
            for x in newlist:
                #print x
                reflist.insert(0, reflist[x])
                reflist.remove(reflist[x])
                
            counter = 0
        default = counter
        for x in reflist[counter:counter+9] :
            nodename = x.nodeName
            if(x.nodeName == 'result'):
                rtype = x.attributes['type'].value
                if(summary and rtype == 'release'):
                    y = x
                    y.toxml()
                    s_node = y.getElementsByTagName('summary')
                    s_msg = s_node[0].firstChild.data
            elif(x.nodeName == 'artist'):
                rtype = 'artist'
            elif(x.nodeName == 'release'):
                rtype = 'release'
            
            x.toxml()
            node = x.getElementsByTagName(iterator)

            if(node.length > 0):
                title = node[0].firstChild.data; #data
                print '[' + str(counter) + '] ' + title + ' [' + rtype + '] '
                if(nodename == 'result' and rtype == 'release' and summary):
                    print '>->->Summary------------------------------------'
                    print s_msg
                    print '------------------------------------------------\n'
                counter += 1
        
        if(counter < reflist.length - 1):
            if(reflist.length > counter + 1):
                print '[-1] See More... (' + str(reflist.length - counter) + ' remaining)'
            elif(x.nodeName == 'result'):
                print 'End Of Search Results'

        input_ = raw_input('\n\nOption [' + str(default) + '] or Filter: ');
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
    new_uri = str.split(str(uri), '?')[0] #Get the url until ? is hit
    (this avoids complications) 
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
    
    return ('http://www.discogs.com/release/' + _id + '?f=xml&api_key=' + api)

def get_snippet(node, tag):
    content = ['temporary']
    reflist = node.getElementsByTagName(tag)
    
    if(reflist != None):
        if(len(reflist) > 0):
            if(tag == 'label' or tag == 'format'): #info is in attributes
                for x in reflist: 
                    title = x.attributes['name'].value
                    #print tag + " Name: " + title
                    content.append(title)
            elif(tag == 'artist'):
                for x in reflist:
                    if(x.parentNode.nodeName != 'extraartists'):
                        title = x.firstChild.firstChild.data
                        #print tag + " Name: " + title
                        content.append(title)
            elif(tag == 'title'): #Only get the first title
                title = reflist[0].firstChild.data
                #print tag + " Name: " + title
                content.append(title)
            else:
                for x in reflist:
                    title = x.firstChild.data
                    #print tag + " Name: " + title
                    content.append(title)
    
        content.remove('temporary')#remove initial declaration
        return content
    else:
        return None
def get_track_list(node):
    content = [['position', 'title', 'duration']]
    reflist = node.getElementsByTagName('track')
    skip = 0
    if(len(reflist) > 0):
        for x in reflist: 
            x.toxml()
            
            reflist = x.getElementsByTagName('position')
            if(reflist > 0 and reflist[0].firstChild != None):
                try:
                    node = reflist[0]
                    position = node.firstChild.data
                except Exception: 
                    position = ''
            else:
                position = ''
                
                
            reflist = x.getElementsByTagName('title')
            if(reflist > 0 and reflist[0].firstChild != None):
                try:
                    node = reflist[0]
                    title = node.firstChild.data
                except:
                    title = ''
            else:
                title = ''
                
            reflist = x.getElementsByTagName('duration')
            if(reflist > 0 and reflist[0].firstChild != None):
                try:
                    node = reflist[0]
                    duration = node.firstChild.data
                except:
                    duration = ''
            else:
                duration = ''
                
            if(skip == 1):
                skip = 0
            else:
                content.append([[position, title, duration]])
    content.remove(['position', 'title', 'duration']) #remove initial declaration
    return content

def build_release(data):
    #First get the artist(s)
    node = data[0]
    node.toxml()
    title = get_snippet(node, 'title')
    artists = get_snippet(node, 'artist')
    labels = get_snippet(node, 'label')
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
    for l in template:
        if(l.startswith('//') or l.find('API') != -1): #If a comment or API
            pass #donothing
        else:
            for a in l:
                if(variable):
                    if(a == 't'):
                        output += title[0]
                        
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
                    elif(a == 'x'):
                        innercounter = len(labels)
                        for x in labels: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '
                    elif(a == 'f'):
                        innercounter = len(formats)
                        for x in formats: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '
                    elif(a == 'c'):
                        innercounter = len(country)
                        for x in country: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '
                    elif(a == 'r'):
                        innercounter = len(released)
                        for x in released: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '
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
                    elif(a == 'g'):
                        innercounter = len(genres)
                        for x in genres: 
                            output += x
                            innercounter -= 1
                            if(innercounter > 0):
                                output += ' , '
                    variable = 0
                else: #If variable is not set
                    if(a == '%'):
                        variable = 1
                    else:
                        output += a
    print output
    print 'Options: '
    print '[0] Save to file ' + title[0] + '.txt'
    print '[1] Do nothing\n\n'
    sel = raw_input( 'Selection [0] : ' )
    if(len(sel) == 0 or sel == 0):
        f = open(title[0] + '.txt', 'w')
        f.write(output.encode('latin-1'))
        f.flush()
        f.close()


if(len(sys.argv) > 1):
    for x in sys.argv:
        if(x[0] != '-'):
            if(search[1] == 'release'):
                try:
                    i_search  = int(x)
                except (TypeError, ValueError):
                    print "**You cannot search releases\n**Please just search normally or use the release indentification number in the future"
                    i_search = release
                    search[1] = 'all'
            else:
                i_search = x
        elif(x == '-s'):
            summary = 1
        elif(x == 'exact'):
            exact = 1
        elif(x == '-url'):
            if(len(i_search) >= 0):
                    i_search = pull_release_id_from_user_url(i_search)
                    search[1] = 'release'
        elif(x == '-release'):
            search[1] = 'release'
        elif(x == '-label'):
            search[1] = 'label'
        elif(x == '-artist'):
            search[1] = 'artist'

initialize()        
while(search[0] != "-99"): 
    
    #Preliminary checks 
    #-------------------------------------------------------------------------------------------------
    if(uri == 'set'):
        uri = raw_input("Enter URL: ")
    if(search[1] == None):
        search[1] = 'all'
    
    #User input_ if needed
    #------------------------------------
    if(i_search == None and uri == None):
        search[0] = raw_input("Search: ")
        explode = str.split(search[0], ' ')
        implode = '' #We'll reconstruct our search query here
        for x in explode:
            if(x == '-release'):
                print "i set release"
                search[1] = 'release'
            elif(x == '-artist'):
                search[1] = 'artist'
            elif(x == '-label'):
                search[1] = 'label'
            elif(x == '-exact'):
                exact = 1
            elif(x == '-s'):
                summary = 1
            elif(x == '-url'):
                if(len(implode) >= 0):
                    i_search = pull_release_id_from_user_url(implode)
                    search[1] = 'release'
            else:
                implode += x + '+'
        
    if(i_search is not None):
        print 'inside..'
        search[0] = i_search
        
        print search[1]
        if(search[1] == 'artist'):
            print search[0]
            if(search[0].startswith('the')):
                split = str.split(search[0], ' ')
                innercounter = 0
                new_s = ''
                for x in split: 
                    if (innercounter > 0):
                        new_s += x + ' '
                new_s += ', The'
                print("Did you mean " + new_s + " ?")
        if(search[1] == 'release'):
            try:
                int(search[0])
                implode = search[0]
            except (TypeError, ValueError):
                print "**You cannot search releases \n**Please use the release ID number in the future"
                search[1] = 'all'
        else:
            explode = str.split(search[0], ' ')
            implode = concat.join(explode)
    #--------------------------------------
        
    if(search[0] == '-99'):
        break
    #--------------------------------------------------------------------------------------------------------
    
    if(uri == None):
        if(search[1] == 'all'):
            uri = 'http://www.discogs.com/search?type=all&q=' + implode + '&f=xml&api_key=' + api
        elif(search[1] == 'artist'):
            uri = 'http://www.discogs.com/artist/' + implode + '?f=xml&api_key=' + api 
        elif(search[1] == 'label'): 
            uri = 'http://www.discogs.com/label/' + implode + '?f=xml&api_key=' + api
        elif(search[1] == 'release'):
            uri = 'http://www.discogs.com/release/' + implode + '?f=xml&api_key=' + api
    
    xmldoc = disc_request(uri)
    doc_type = xmldoc.firstChild.firstChild.nodeName
    
    if(search[1] == 'all'): 
        if(exact):
            reflist = xmldoc.getElementsByTagName('exactresults')
            if(reflist < 1): 
                reflist = xmldoc.getElementsByTagName('result')
            node = reflist[0]
            node.toxml()
            reflist = node.getElementsByTagName('result') #This is the parent node to look in (result)
        else:
            reflist = xmldoc.getElementsByTagName('result')
            
            
        if(reflist.length < 1):
            print('nothing')
            i_search = None
            uri = None
        else:
            selected = search_menu(reflist, 'title') #This tells the function to show a menu using the TITLE as options
            node = reflist[int(selected)]
            rtype = node.attributes['type'].value
            node.toxml()
            uri_node = node.getElementsByTagName('uri')
            if(rtype == 'artist'):
                uri = get_artist_uri(uri_node[0])
                search[1] = 'artist'
            elif(rtype == 'release'):
                uri = get_release_uri(uri_node[0])
                search[1] = 'release'
    elif(doc_type == 'label'):
        reflist = xmldoc.getElementsByTagName('release')
        if(reflist.length < 1):
            print('nothing')
        else:
            selected = search_menu(reflist, 'title')
            title = reflist[int(selected)].getElementsByTagName('title')
            if(len(title) > 0):
                i_search = title
                uri = None
            else:
                print "Can't use this data to process your request"
                i_search = None
                uri = None
    elif(doc_type == 'artist'):
        reflist = xmldoc.getElementsByTagName('artist')
        if(reflist.length < 1):
            print('nothing')
            i_search = None
            uri = None
        elif(reflist.length > 1):
            selected = search_menu(reflist, 'name')
            node = reflist[int(selected)]
            uri = get_artist_uri(uri_node)
            xmldoc = disc_request(uri) #this will return the artist page
            reflist = xmldoc.getElementsByTagName('artist')
            node = reflist[0]
        else:
            node = reflist[0]
        
        
        reflist = xmldoc.getElementsByTagName('release')
        selection = search_menu(reflist, 'title')
        id_ = reflist[int(selected)].attributes['id'].value
        
        print "id: " + id_
        i_search = id_
        search[1] = 'release'
        uri = None
    elif(doc_type == 'release'):
        node = xmldoc.getElementsByTagName('release')
        build_release(node)
        i_search = None
        uri = None
        search[1] = 'all'
    else:
        print 'Discogs returned an Unknown XML file'
        print doc_type
        doc_type = None
        i_search = None
        uri = Nonertype = x.attributes['type'].value
