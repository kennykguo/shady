%{
/* convert shader text into tokens. */

#include <stdlib.h>
#include <errno.h>
#include <limits.h>
#include <float.h>
#include <math.h>
#include <string.h>

#include "common.h"
#include "ast.h"
#include "parser.tab.h"

#define YY_USER_INIT { yyin = inputFile; }
#define yyinput      input
#define yERROR(x)    { fprintf(errorFile, "\nLEXICAL ERROR, LINE %d: %s\n", yyline, x); errorOccurred = 1; }
#define yOUT(x)      { return x; }

/* declare functions before use. */
int ParseComment(void);
int ParseInt(void);
int ParseFloat(void);
int ParseIdent(void);
int yyline = 1;

%}
%option noyywrap nounput

%%

"/*"                          { if(!ParseComment()) { yyterminate(); } }
"//"[^\n]*                    { /* skip the line comment. */ }

[ \t]                         { }
\r?\n                         { yyline++; }
<<EOF>>                       { yyterminate(); }

[+\-*/\^]                     { yOUT(yytext[0]); }
[()[\]{}]                     { yOUT(yytext[0]); }
[<>=!]                        { yOUT(yytext[0]); }
";"                           { yOUT(yytext[0]); }
","                           { yOUT(yytext[0]); }
"&&"                          { yOUT(AND); }
"||"                          { yOUT(OR); }
"!="                          { yOUT(NEQ); }
"<="                          { yOUT(LEQ); }
">="                          { yOUT(GEQ); }
"=="                          { yOUT(EQ); }

const                         { yOUT(CONST); }
bool                          { yOUT(BOOL_T); }
int                           { yOUT(INT_T); }
float                         { yOUT(FLOAT_T); }
vec(2|3|4)                    { yylval.as_vec = yytext[3] - '1'; yOUT(VEC_T); }
ivec(2|3|4)                   { yylval.as_vec = yytext[4] - '1'; yOUT(IVEC_T); }
bvec(2|3|4)                   { yylval.as_vec = yytext[4] - '1'; yOUT(BVEC_T); }

if                            { yOUT(IF); }
else                          { yOUT(ELSE); }

dp3                           { yylval.as_func = 0; yOUT(FUNC); }
rsq                           { yylval.as_func = 2; yOUT(FUNC); }
lit                           { yylval.as_func = 1; yOUT(FUNC); }
sin                           { yylval.as_func = SIN; yOUT(FUNC); }
cos                           { yylval.as_func = COS; yOUT(FUNC); }
fract                         { yylval.as_func = FRACT; yOUT(FUNC); }
abs                           { yylval.as_func = ABS; yOUT(FUNC); }

true                          { yOUT(TRUE_C); }
false                         { yOUT(FALSE_C); }

0                             { yylval.as_int = 0; yOUT(INT_C); }                  
[1-9][0-9]*                   { if (ParseInt()) { yOUT(INT_C); } }

(0|([1-9][0-9]*))\.[0-9]*     { if (ParseFloat()) { yOUT(FLOAT_C); } }
\.[0-9]+                      { if (ParseFloat()) { yOUT(FLOAT_C); } }

[A-Za-z_][A-Za-z0-9_]*        { if (ParseIdent()) { yOUT(ID); } }


0[0-9]+                       { yERROR("Octal numbers are not allowed.");  yyterminate(); }
[0-9]+[a-zA-Z_]+              { yERROR("Integers and identifiers/keywords must be separated by whitespace.");  yyterminate(); }
.                             { yERROR("Unknown token");  yyterminate(); }

%%

/* define the function token values. */
enum {
  MAX_INT_LIT = (1 << 21) - 1,
  MIN_INT_LIT = -MAX_INT_LIT,
  MAX_IDENT_LEN = 32
};

/* read a block comment and update the line count. */
int ParseComment(void) {
    int previous = 0;
    int start_line = yyline;
    int current;
    /* the scanner returns zero at the end of input. */
    while ((current = yyinput()) != 0) {
        if (current == '\n') yyline++;
        if (previous == '*' && current == '/') return 1;
        previous = current;
    }
    fprintf(errorFile, "\nLEXICAL ERROR, LINE %d: Unmatched /*\n", start_line);
    errorOccurred = 1;
    return 0;
}

/* convert text into an integer token. */
int ParseInt(void) {
  errno = 0;
  long num = strtol(yytext, NULL, 10);
  if(ERANGE == errno) {
    if(LONG_MAX == num || LONG_MIN == num) {
      yERROR("Integer literal is out of range (case 1).");
      return 0;
    }
  }

  if(MAX_INT_LIT < num || MIN_INT_LIT > num) {
    yERROR("Integer literal is out of range (case 2).");
    return 0;
  }

  yylval.as_int = (int) num;
  return 1;
}

/* convert text into a floating point token. */
int ParseFloat(void) {
  errno = 0;
  double num = strtod(yytext, NULL);
  
  if(ERANGE == errno) {
    if(HUGE_VAL == num || -HUGE_VAL == num) {
      yERROR("Floating point literal is out of range (case 1).");
      return 0;
    }
  }

  /* reject values that are not numbers. */
  if(num != num) {
    yERROR("Floating point literal is NaN.");
    return 0;
  }

  /* reject overflow. this check does not reject underflow. */
  if(FLT_MAX < num || -FLT_MAX > num) {
    yERROR("Floating point literal is out of range (case 2).");
    return 0;
  }  

  yylval.as_float = (float) num;
  return 1;
}

/* copy the text for an identifier token. */
int ParseIdent(void) {
  if(MAX_IDENT_LEN < yyleng) {
    yERROR("Identifier is too long.");
    return 0;
  }

  char *ident = (char *) calloc(yyleng + 1, sizeof(char));
  memcpy(ident, yytext, yyleng);

  yylval.as_str = ident;
  return 1; 
}

