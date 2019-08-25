import sys
import requests
import time
from urllib.parse import urlparse
from xml.etree import ElementTree

savePath = "C:\\Temp\\"

numArguments = len(sys.argv)
arrArguments = sys.argv

def urlParse(o):
    # to extract filename from s3 link
    urlFilePath = urlparse(o).path
    filename = urlFilePath[urlFilePath.rfind("%2F")+3:]
    return filename


def urlDownload(url, filename):
    # to download file from link
    with open(savePath+filename, 'wb') as f:
        try:
            response = requests.get(url, stream=True)
        except requests.exceptions.RequestException as err:
            # no response from server DNS, timeout ..  
            print("URL DOWNLOAD ERROR [INFO]\t: No response from the server. Make sure URL is correct.")
            print("URL DOWNLOAD ERROR [DEBUG]\t: Error message",err)
            sys.exit(1)

        totalSize = response.headers.get('content-length')
        status_code = response.status_code
        if totalSize is None:
            # server responded but with error
            tree = ElementTree.fromstring(response.content)
            print("URL DOWNLOAD ERROR [INFO]\t: Make sure URL is correct. Server response ", status_code)
            print("URL DOWNLOAD ERROR [DEBUG]\t: Error message", tree.find('Message').text)
            sys.exit(1)
        elif int(totalSize) == 0:
            # server responded but downloaded file of Zero size
            print("URL DOWNLOAD ERROR [INFO]\t: Zero file size")
            sys.exit(1)
        else:
            # start downloading file
            downloadedSize = 0
            downloadTime = 0
            totalSize = int(totalSize)
            stopTime = time.time()
            sys.stdout.write('\n')
            for chunkData in response.iter_content(chunk_size=max(int(totalSize/1000), 1024*1024)):
                startTime = time.time()
                downloadedSize += len(chunkData)
                f.write(chunkData)
                done = int(20*downloadedSize/totalSize)     # scale size of 20 parrots
                chunkTime = startTime - stopTime            # time took last chunk to download 
                speed = len(chunkData) / chunkTime
                downloadTime += chunkTime                   # total download time
                sys.stdout.write('\r{}\t[{}>{}]\t{} of {}M \t\t{}MB/s \tin {}s'.format(
                    filename, 
                    '=' * done, 
                    ' ' * (20-1-done), 
                    round(downloadedSize/1024/1024,2), 
                    round(totalSize/1024/1024,2), 
                    round(speed/1024/1024,2), 
                    round(downloadTime)))
                sys.stdout.flush()
                stopTime = time.time()
            sys.stdout.write('\n')

def fileType(filename):
    # attempt to identify file type from the link - sysdump, config backup, saveCdb, ...
    if "SysDump" in filename:
        print("sysdump")
    elif "config" in filename:
        print("config backup")
    elif "saveCdb" in filename:
        print("savecdb")
    else:
        print("unknown")

if (numArguments == 2):
    # make sure we receive the only argument
    url = str(arrArguments[1])
    filename = urlParse(url)
    urlDownload(url, filename)
    fileType(filename)
else:
    print("specify url as the only argument")
