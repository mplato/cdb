import sys
import requests
from urllib.parse import urlparse
from xml.etree import ElementTree


numArguments = len(sys.argv)
arrArguments = sys.argv


def urlParse(o):
    # to extract filename from s3 url
    path = urlparse(o).path
    filename = path[path.rfind("%2F")+3:]
    return filename


def urlDownload(url, filename):
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            tree = ElementTree.fromstring(response.content)
            print("URL DOWNLOAD ERROR: ",tree.find('Message').text)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format(
                    '█' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


if (numArguments == 2):
    # make sure we receive the only argument
    url = str(arrArguments[1])
    filename = urlParse(url)
    urlDownload(url, filename)
else:
    print("specify url as the only argument")
