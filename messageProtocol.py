class messageProtocol:
    def __init__(self, pCode, fList, fName, msg):
        # protocol code: 0 = registry to network
        #               1 = registry new files to server's storage
        #               2 = request file from server, server return list of hostname that own the file
        #                                           , otherwise return a reject message
        #               3 = logout from network
        #              10 =
        #              30 = reject message
        # file List: [file1.type, file2.type, file3.type]
        # file name: file4.type
        # msg      : String

        self.pCode = pCode
        self.fList = fList
        self.fName = fName
        self.msg = msg

    def getpCode(self):
        return self.pCode

    def getfList(self):
        return self.fList

    def getfName(self):
        return self.fName

    def getmsg(self):
        return self.msg