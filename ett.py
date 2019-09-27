import sys
import requests
import time
import datetime
import tarfile
import os
import shutil
from urllib.parse import urlparse
from xml.etree import ElementTree

savePath = "C:/Temp/"
tmpdir = savePath+"cdb-"+str(time.time())+"/"

def createTmpDir(tmpdir):
    os.mkdir(tmpdir)

def removeTmpDir(tmpdir):
    shutil.rmtree(tmpdir)

numArguments = len(sys.argv)
arrArguments = sys.argv

def urlParse(o):
    """ to extract filename from s3 link """
    urlFilePath = urlparse(o).path
    filename = urlFilePath[urlFilePath.rfind("%2F")+3:]
    return filename


def urlDownload(url, filename):
    """ to download file from link """
    with open(tmpdir+filename, 'wb') as f:
        try:
            response = requests.get(url, stream=True)
        except requests.exceptions.RequestException as err:
            # no response from server DNS, timeout ..  
            print("URL DOWNLOAD ERROR [INFO]\t: No response from the server. Make sure URL is correct.")
            print("URL DOWNLOAD ERROR [DEBUG]\t: Error message",err)
            removeTmpDir(tmpdir)
            sys.exit(1)
            
        totalSize = response.headers.get('content-length')
        status_code = response.status_code
        if totalSize is None:
            # server responded but with error
            tree = ElementTree.fromstring(response.content)
            print("URL DOWNLOAD ERROR [INFO]\t: Make sure URL is correct. Server response ", status_code)
            print("URL DOWNLOAD ERROR [DEBUG]\t: Error message", tree.find('Message').text)
            removeTmpDir(tmpdir)
            sys.exit(1)
        elif int(totalSize) == 0:
            # server responded but downloaded file of Zero size
            print("URL DOWNLOAD ERROR [INFO]\t: Zero file size")
            removeTmpDir(tmpdir)
            sys.exit(1)
        else:
            # start downloading file
            downloadedSize = 0
            downloadTime = 0
            remainingTime = 0
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
                remainingTime = (totalSize - downloadedSize)/speed
                sys.stdout.write('\r{}\t[{}>{}]\t{} of {}M \t\t{}MB/s \tremain {}'.format(
                    filename, 
                    '=' * done, 
                    ' ' * (20-1-done), 
                    round(downloadedSize/1024/1024,2), 
                    round(totalSize/1024/1024,2), 
                    round(speed/1024/1024,2), 
                    str(datetime.timedelta(seconds=round(remainingTime)))))
                sys.stdout.flush()
                stopTime = time.time()
            sys.stdout.write('\n')

def fileType(filename):
    """ attempt to identify file type from the link - sysdump, config backup, saveCdb, ... """
    typeArray = ['unknown','sysDump','configBackup']
    fileType = 0
    if "SysDump" in filename:
        fileType = 1
    elif ("config" in filename) and ("config_export" not in filename):
        fileType = 2
    else:
        fileType = 0

    #ask user to specify file type    
    print("\n----------------------\nWHAT TYPE OF FILE IS IT?\n-----------------------\n")
    print("[1] SysDump (*default)\n" if fileType == 1 else "[1] SysDump\n")
    print("[2] Config Backup (*default)\n" if fileType == 2 else "[2] Config Backup\n")
    userFileType =  input("\nEnter: ")

    if (userFileType.isdigit()) and (0 < int(userFileType) < len(typeArray)):
        # user made valid choice
        return typeArray[int(userFileType)]
    elif (fileType != 0):
        # no user choice but fileType being identified by url
        return typeArray[fileType]
    else :
        # unknown fileType
        print("FILE TYPE ERROR [DEBUG]\t: File Type Not Identified")
        removeTmpDir(tmpdir)
        sys.exit(1) 

def fileExtract(filename,filetype):
    """ depending on filetype extract version and cdb files """
    archive = tarfile.open(tmpdir+filename, 'r')
    for item in archive.getmembers():

        if filetype == "sysDump":
            # looking for database.tgz
            if "database.tgz" in item.name:
                archive.extract(item, tmpdir)
                #print("extracted ",tmpdir+item.name)
                databaseArchive = tarfile.open(tmpdir+item.name, 'r')
                for item2 in databaseArchive.getmembers():
                    #looking for saveCdb.tar
                    if "database/saveCdb.tar" in item2.name:
                        databaseArchive.extract(item2,tmpdir)
                        #print("extracted ",tmpdir+item2.name)
                        saveCdbArchive = tarfile.open(tmpdir+item2.name, 'r')
                        saveCdbArchive.extractall(tmpdir+"cdb")
                        print("SUCCESS FILES EXTRACTED[INFO]: Cdb files have been extracted and stored ",tmpdir+"cdb")
                        break
                break
        elif filetype == "configBackup":
            # looking for cdb archive 
            if ("cdb" in item.name) and ("tar.gz" in item.name):
                archive.extract(item,tmpdir)
                cdbArchive = tarfile.open(tmpdir+item.name, 'r')
                cdbArchive.extractall(tmpdir+"cdb")
                print("SUCCESS FILES EXTRACTED[INFO]: Cdb files have been extracted and stored ",tmpdir+"cdb")
                break
        else:
            print("FILE EXTRACT ERROR[INFO]\t: File type can't be recognized during extraction")
            removeTmpDir(tmpdir)   
            sys.exit(1)
    return 0

def sbxVersion():
    """ input sbx version"""
    return 0

if (numArguments == 2):
    # make sure we receive the only argument
    url = str(arrArguments[1])
    createTmpDir(tmpdir)
    # extract file name from url
    filename = urlParse(url)
    # download file
    urlDownload(url, filename)
    # guess and ask for file type
    filetype = fileType(filename)
    # extract tgz
    fileExtract(filename,filetype)
    version = sbxVersion()
    #removeTmpDir(tmpdir)
else:
    print("specify url as the only argument")
