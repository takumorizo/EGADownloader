#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import sys
import requests
import errno
import traceback
from time import sleep
import re

class EGAClient(object):
    """docstring for EGAClient"""
    def __init__(self, user, password,
                 accessURL   = u'https://ega.ebi.ac.uk/ega/rest/access/v2', \
                 downloadURL = u'http://ega.ebi.ac.uk/ega/rest/download/v2'):
        super(EGAClient, self).__init__()
        self.__accessURL   = accessURL
        self.__downloadURL = downloadURL
        self.__user        = user
        self.__password    = password
        self.__session     = None

    def repeat(count):
        def _decorator(fun):
            def _decorated_fun(*args, **kwargs):
                for i in range(count):
                    code, ans = fun(*args, **kwargs)
                    if code.startswith(u'2'):
                        return (code, ans)
                    else:
                        print(u'Request failed with code:' + str(code), file=sys.stderr)
                        sleep(600)
                    print(u'count:' + str(i) + '/' + str(count), file=sys.stderr)
                raise Exception(u'Invalid return code. Try by ' + str(count) + ' times.')
            return _decorated_fun
        return _decorator

    def access(func):
        def inner(self, *args, **kwargs):
            code, session = self.prepareSession()
            self.__session = session
            return func(self, *args, **kwargs)
        return inner

    def tickets(func):
        def inner(self, *args, **kwargs):
            code, result = func(self, *args, **kwargs)
            return code, self.__obtainTickets(result)
        return inner

    @repeat(count = 5)
    def prepareSession(self):
        res = requests.get(self.__accessURL + u'/users/' + str(self.__user),{u'pass':self.__password})
        response = res.json()
        code    = response[u'header'][u'code']
        session = response[u'response'][u'result'][1]
        return (code, session)

    @repeat(count = 5)
    @access
    def listFiles(self, datasetID):
        print(u'accessing the list of files available...', file=sys.stderr)
        res = requests.get(self.__accessURL + u'/datasets/' + str(datasetID) + u'/files', {u'session':self.__session})
        code   = self.__obtainCode(res)
        result = self.__obtainResult(res)
        return (code, result)

    @repeat(count = 5)
    @access
    def requestFile(self, encryptionKey, fileID, descriptor):
        print(u'requesting files, fileID: ' + str(fileID), file=sys.stderr)
        data = u'downloadrequest={{"rekey":{},"downloadType":"STREAM","descriptor":{}}}'.format(encryptionKey, descriptor)
        res = requests.post(self.__accessURL + u'/requests/new/files/' + str(fileID),
                            params = {u'session':self.__session},
                            data = data)
        print(res.json(), file=sys.stderr)
        code   = self.__obtainCode(res)
        result = self.__obtainResult(res)
        return (code, result)

    @repeat(count = 5)
    @access
    @tickets
    def requestTickets(self, descriptor):
        print(u'requesting tickets...', file=sys.stderr)
        res = requests.get(self.__accessURL + u'/requests/' + str(descriptor) + u'/files', params = {u'session':self.__session})
        print(res.json(), file=sys.stderr)
        code   = self.__obtainCode(res)
        result = self.__obtainResult(res)
        return (code, result)

    @repeat(count = 5)
    @access
    def downloadTickets(self, tickets, fileName):
        # headers = {'Accept': 'application/octet-stream'}
        res = requests.get(self.__downloadURL + u'/downloads/' + str(tickets),
                           params = {u'session':self.__session},
                           stream = True)

        if res.status_code == 200:
            with open(fileName, 'wb') as file:
                for chunk in res.iter_content(chunk_size=4096):
                    file.write(chunk)

        code   = self.__obtainCode(res)
        result = None
        return (code, result)

    def __obtainCode(self, response):
        return str(response.status_code)

    def __obtainResult(self, response):
        return response.json()[u'response'][u'result']

    def __obtainTickets(self, result):
        return [ res[u'ticket'] for res in result ]

def listFilesInDataSet(argvs):
    userName   = argvs[1]
    password   = argvs[2]
    datasetID  = argvs[3]

    client = EGAClient(userName, password)
    code, results = client.listFiles(datasetID)
    print(u'fileDataset\tfileIndex\tfileMD5\tfileName\tfileStatus\tfileSize\tfileID')

    for eachFile in results:
        items = []
        for key in [u'fileDataset', u'fileIndex', u'fileMD5', u'fileName', u'fileStatus', u'fileSize', u'fileID']:
            if key in eachFile:
                items.append(eachFile[key])
            else:
                items.append('')
        outputString = '\t'.join(map(str, items))
        outputString = outputString.replace('\n', '')
        print(outputString)

def downloadEncryptedFile(argvs):
    userName   = argvs[1]
    password   = argvs[2]
    fileID     = argvs[3]
    encriptKey = argvs[4]
    fileName   = argvs[5]

    print(u'fileName', file=sys.stderr)
    print(fileName,   file=sys.stderr)

    folder =  os.path.dirname(fileName)
    print(u'folder', file=sys.stderr)
    print(folder,   file=sys.stderr)
    try:
        print(u'Making directory...', file=sys.stderr)
        os.makedirs(folder)
    except OSError as e:
        if e.errno == errno.EEXIST:
            print(u'Directory already exists.', file=sys.stderr)
        else:
            raise

    while True:
        try:
            client = EGAClient(userName, password)
            code, results = client.requestFile(encriptKey, fileID, fileID + u'_test')
            code, tickets = client.requestTickets(fileID + u'_test')
            print(tickets, file=sys.stderr)
            # assert len(tickets) == 1
            for ticket in tickets:
                client.downloadTickets(ticket, fileName)
            break
        except Exception as e:
            sleep(600)
            print(u'Exception occurred.', file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)

    print(u'End download.', file=sys.stderr)

def parseNodes(node, tag):
    ans = []
    if node.tag == tag:
        ans.append(node)
    for child in node:
        ans.extend(parseNodes(child, tag))
    return ans

def listMetaData(argvs):
    xmlDir     = argvs[1]
    files = os.listdir(xmlDir)
    searchAttributes = [u'filename', u'checksum_method', u'checksum', u'unencrypted_checksum']
    print(u'#filename\tchecksum_method\tchecksum\tunencrypted_checksum')
    from xml.etree import ElementTree
    for file in files:
        xmlFile = xmlDir + u'/' + file
        tree = ElementTree.parse(xmlFile)
        fileNodes = parseNodes(tree.getroot(), u'FILE')
        for fileNode in fileNodes:
            outputList = []
            for attrKey in searchAttributes:
                if attrKey in fileNode.attrib:
                    outputList.append(fileNode.attrib[attrKey])
                else:
                    outputList.append(u'NA')
            outputString = u'\t'.join(map(str, outputList))
            outputString = outputString.replace(u'\n', u'')
            print(outputString)

def checkMD5(argvs):
    givenMD5     = argvs[1]
    md5Set = set([])
    for line in sys.stdin:
        if line.startswith(u'#'):
            continue
        line = line.replace(u'\n',u'')
        line = line.replace(u'\r',u'')
        lineCols = re.split(u'\t',line)
        md5Set.add(lineCols[2])
        md5Set.add(lineCols[3])

    print(u'givenMD5', file=sys.stderr)
    print(givenMD5,    file=sys.stderr)
    print(u'md5Set',   file=sys.stderr)
    print(md5Set,      file=sys.stderr)
    if givenMD5 in md5Set:
        print(u'givenMD5 is included within the metaData')
    else:
        print(u'givenMD5 is not included within the metaData')
        raise Exception(u'Unmatch md5 check sum.')

def main():
    argvs = sys.argv
    mode  = argvs[1]
    if mode == u'listFiles':
        listFilesInDataSet(argvs[1:len(argvs)])
    elif mode == u'downloadFile':
        downloadEncryptedFile(argvs[1:len(argvs)])
    elif mode == u'listMetaData':
        listMetaData(argvs[1:len(argvs)])
    elif mode == u'checkMD5':
        checkMD5(argvs[1:len(argvs)])
    else:
        raise Exception(u'Invalid mode.')



if __name__ == '__main__':
    main()
