#ifndef __THESIS_API_H
#define __THESIS_API_H

extern "C" unsigned long long __thesis_getUserTime();
extern "C" void __thesis_LogTiming(unsigned long long entryTime, const char *FuncName);

#endif