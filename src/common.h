/* share input and diagnostic streams between compiler stages. */
#ifndef SHADY_COMMON_H
#define SHADY_COMMON_H

#include <stdio.h>

extern FILE *inputFile;
extern FILE *errorFile;
extern int errorOccurred;

#endif
