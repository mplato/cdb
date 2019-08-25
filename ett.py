import sys
from urllib.parse import urlparse

numArguments = len(sys.argv)
arrArguments = sys.argv

def parseUrl(o):
    # to extract filename from s3 url
    path = urlparse(o).path
    filename = path[path.rfind("%2F")+3:]
    return filename
 
if (numArguments == 2):
    # make sure we receive the only argument
    url = str(arrArguments[1])
    print("\n",parseUrl(url))
else:
    print("specify url as the only argument")
