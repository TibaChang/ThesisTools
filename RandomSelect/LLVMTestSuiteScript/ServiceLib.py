#!/usr/bin/python3
import os
import sys
from time import gmtime, strftime, localtime
from datetime import datetime, date, timedelta
import LitMimic as lm
import smtplib

class TimeService:
    DateTimeFormat = "%Y%m%d_%H-%M-%S"
    def GetCurrentLocalTime(self):
        return strftime(self.DateTimeFormat, localtime())

    def GetDeltaTimeInDate(self, prev, post):
        t1 = datetime.strptime(prev, self.DateTimeFormat)
        t2 = datetime.strptime(post, self.DateTimeFormat)
        delta = t2 - t1
        return delta

    def DelTimeStamp(self):
        ResultDir = os.getenv('LLVM_THESIS_Random_LLVMTestSuite_Results')
        if not os.path.exists(ResultDir):
            os.makedirs(ResultDir)
        timeFile = ResultDir + "/TimeStamp"
        if os.path.isfile(timeFile):
            os.remove(timeFile)

class LogService():
    StderrFilePath = None
    StdoutFilePath = None
    RecordFilePath = None
    SanityFilePath = None
    ErrorSetFilePath = None
    time = None
    TimeStamp = None
    def __init__(self):
        self.TimeStamp = os.getenv('LLVM_THESIS_Random_LLVMTestSuite_Results') + "/TimeStamp"
        if os.path.isfile(self.TimeStamp):
            #later enter
            with open(self.TimeStamp, 'r') as file:
                self.time = file.read()
                file.close()
        else:
            #first enter
            time = TimeService()
            self.time = time.GetCurrentLocalTime()
            with open(self.TimeStamp, 'w') as file:
                file.write(self.time)
                file.close()

        Loc = os.getenv('LLVM_THESIS_Random_LLVMTestSuite_Results', "/tmp")
        if(Loc == "/tmp"):
            mail = drv.EmailService()
            mail.SignificantNotification(Msg="Log dir=\"{}\"\n".format(Loc))
        else:
            os.system("mkdir -p "+ Loc)

        self.StdoutFilePath = Loc + '/' + self.time + "_STDOUT"
        self.StderrFilePath = Loc + '/' + self.time + "_STDERR"
        self.RecordFilePath = Loc + '/' + self.time + "_Time"
        self.SanityFilePath = Loc + '/' + self.time + "_ErrorTest"
        self.ErrorSetFilePath = Loc + '/' + self.time + "_ErrorSet"

    def out(self, msg):
        print(msg, end="")
        #save to same file for every instance
        with open(self.StdoutFilePath, "a") as file:
            file.write(msg)
            file.close()

    def outNotToFile(self, msg):
        print(msg, end="")

    def err(self, msg):
        #save to same error file for every instance
        with open(self.StderrFilePath, "a") as file:
            file.write(msg)
            file.close()

    def record(self, msg):
        #save to same file for every instance
        with open(self.RecordFilePath, "a") as file:
            file.write(msg)
            file.close()

    def sanityLog(self, msg):
        #save to same file for every instance
        with open(self.SanityFilePath, "a") as file:
            file.write(msg)
            file.close()

    def ErrorSetLog(self, msg):
        #save to same file for every instance
        with open(self.ErrorSetFilePath, "a") as file:
            file.write(msg)
            file.close()

class EmailService:
    def send(self, Subject, Msg, To="jaredcjr.tw@gmail.com"):
        TO = To
        SUBJECT = Subject
        TEXT = Msg
        # Gmail Sign In
        gmail_sender = 'sslab.cs.nctu@gmail.com'
        gmail_passwd = '2018graduate'

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_sender, gmail_passwd)

        BODY = '\r\n'.join(['To: %s' % TO,
                            'From: %s' % gmail_sender,
                            'Subject: %s' % SUBJECT,
                            '', TEXT])
        Log = LogService()
        try:
            server.sendmail(gmail_sender, [TO], BODY)
            Log.out('Email sent!\n')
        except:
            Log.out('Error sending mail\n')
            Log.err('Error sending mail\n')
        server.quit()

    def SignificantNotification(self, To, Msg):
        MailSubject = "LitDriver Notification."
        self.send(To=To, Subject=MailSubject, Msg=Msg)

class BenchmarkNameService:
    def ReplaceWithDash(self, str):
        ret = ""
        for c in str:
            if c != '/':
                ret += c
            else:
                ret += '-'
        return ret

    def GetFormalName(self, full_path):
        tests = lm.TargetBenchmarks()
        ret = full_path
        for RemoveWords in tests.TargetPathList:
            if ret.startswith(RemoveWords):
                ret = ret[len(RemoveWords):]
                break
        if ret.startswith("./"):
            ret = ret["./"]
        return self.ReplaceWithDash(ret)

    def RemoveSanityFailedTestDesc(self, SanityFile):
        Log = LogService()
        FailList = []
        TargetPrefix = "    test-suite :: "
        with open(SanityFile, 'r') as file:
            for line in file:
                if line.startswith(TargetPrefix) :
                    FailList.append(line[len(TargetPrefix):])
            file.close()
        pwd = os.getcwd()
        LLVMTestSuiteBuildPath = os.getenv('LLVM_THESIS_TestSuite', "Error")
        os.chdir(LLVMTestSuiteBuildPath)

        # Create InputSet dict
        RandomSetAllLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSetAll"
        InputSetDict = {}
        with open(RandomSetAllLoc, "r") as file:
            for line in file:
                Set = [x.strip() for x in line.split(',')]
                InputSetDict[Set[0]] = Set[1]

        for test in FailList:
            os.remove(test)
            Log.sanityLog("Remove: " + test)
            # Log the error set for the corresponding application
            ErrorSet = InputSetDict[LLVMTestSuiteBuildPath + "/" + test]
            Log.ErrorSetLog(test + ", " + ErrorSet)

        os.chdir(pwd)

    def RemoveFailureRecords(self, StdoutFile, RecordFile):
        Log = LogService()
        FailList = []
        TargetPrefix = "    test-suite :: "
        with open(StdoutFile, 'r') as file:
            for line in file:
                if line.startswith(TargetPrefix) :
                    FailList.append(line[len(TargetPrefix):])
            file.close()
        #get the targets
        FailNameList = []
        for line in FailList:
            PathPrefix = line[:line.rfind('/')]
            PathPostfix = line[line.rfind('/') + 1:]
            NamePostfix = PathPrefix[PathPrefix.rfind('/') + 1:] + '-' + PathPostfix
            #remove .test
            NamePostfix = NamePostfix[:-(len(".test") + 1)]
            FailNameList.append(NamePostfix.rstrip())
        #remove form records
        NewRecord = ""
        with open(RecordFile, 'r') as file:
            for line in file:
                LinePrefix = line[:line.find(',')]
                RmFlag = False
                for RemoveTarget in FailNameList:
                    if LinePrefix.endswith(RemoveTarget):
                        RmFlag = True
                        break
                if RmFlag == False:
                    NewRecord += line
            file.close()

        #replace the original one
        with open(RecordFile, 'w') as file:
            file.write(NewRecord)
            file.close()

class ReadPassSetService:
    def ReadCorrespondingSet(self, elfPath):
        RandomSetLoc = os.getenv('LLVM_THESIS_RandomHome') + "/InputSetAll"
        RandomSets = []
        try:
            with open(RandomSetLoc, "r") as file:
                for line in file:
                    RandomSets.append(line.split(","))
                file.close()

            RandomSet = "Error"
            for Set in RandomSets:
                if elfPath.startswith(Set[0]):
                    RandomSet = Set[1].lstrip().rstrip()
            if RandomSet == "Error":
                mail = EmailService()
                mail.send(Subject="Error Logging PassSet", Msg="Check it:\n{}\n".format(elfPath))
        except:
            RandomSet = "Error"

        return RandomSet
