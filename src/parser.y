%{
/* parse shader tokens and build the syntax tree. */

#include <string.h>
#include <stdlib.h>

#include "common.h"
#include "ast.h"
#include "symbol.h"
#include "semantic.h"


void yyerror(const char *message);
int yylex();
extern int yyline;

%}

%define parse.error detailed

%union {
  int as_int;
  int as_vec;
  float as_float;
  char *as_str;
  int as_func;
  node *as_ast;
}

%token          FLOAT_T
%token          INT_T
%token          BOOL_T
%token          CONST
%token          FALSE_C TRUE_C
%token          IF ELSE
%token          AND OR NEQ EQ LEQ GEQ

%token <as_vec>   VEC_T
%token <as_vec>   BVEC_T
%token <as_vec>   IVEC_T
%token <as_float> FLOAT_C
%token <as_int>   INT_C
%token <as_str>   ID
%token <as_func> FUNC

%left     OR
%left     AND
%left     EQ NEQ '<' LEQ '>' GEQ
%left     '+' '-'
%left     '*' '/'
%right    '^'
%right    '!' UMINUS
%left     '(' '['

%left     WITHOUT_ELSE
%left     WITH_ELSE

%type <as_ast> program
%type <as_ast> scope
%type <as_ast> statement_list
%type <as_ast> declaration
%type <as_ast> statement
%type <as_ast> type
%type <as_ast> expression
%type <as_ast> variable
%type <as_ast> arguments
%type <as_ast> arguments_opt

%expect 1

%destructor { free($$); } <as_str>
%destructor { ast_free($$); } <as_ast>

%start program

%%

program
  : scope 
      { ast = $1; $$ = NULL; /* the main function owns the completed tree. */ }
  ;

scope
  : '{' statement_list '}'
      { // separate declarations from statements. this changes mixed source order.
        node *decls = NULL;
        node *stmts = NULL;
        node *curr = $2;
        
        while (curr) {
            node *item = curr->list.item;
            node *next = curr->list.next;
            
            if (item && item->kind == DECLARATION_NODE) {
                // add the declaration to its list.
                node *new_decl = ast_allocate(DECLARATIONS_NODE, item, decls);
                decls = new_decl;
            } else if (item) {
                // add the statement to its list.
                node *new_stmt = ast_allocate(STATEMENTS_NODE, item, stmts);
                stmts = new_stmt;
            }
            free(curr);
            curr = next;
        }
        
        $$ = ast_allocate(SCOPE_NODE, decls, stmts); }
  ;

statement_list
  : statement_list statement
      { $$ = ast_allocate(STATEMENTS_NODE, $2, $1); }
  | statement_list declaration
      { $$ = ast_allocate(STATEMENTS_NODE, $2, $1); }
  | 
      { $$ = NULL; }
  ;

declaration
  : type ID ';' 
      { $$ = ast_allocate(DECLARATION_NODE, 0, $1, $2, NULL); }
  | type ID '=' expression ';'
      { $$ = ast_allocate(DECLARATION_NODE, 0, $1, $2, $4); }
  | CONST type ID '=' expression ';'
      { $$ = ast_allocate(DECLARATION_NODE, 1, $2, $3, $5); }
  ;


statement
  : variable '=' expression ';'
      { $$ = ast_allocate(ASSIGNMENT_NODE, $1, $3); }
  | IF '(' expression ')' statement ELSE statement %prec WITH_ELSE
      { $$ = ast_allocate(IF_STMT_NODE, $3, $5, $7); }
  | IF '(' expression ')' statement %prec WITHOUT_ELSE
      { $$ = ast_allocate(IF_STMT_NODE, $3, $5, NULL); }
  | scope 
      { $$ = $1; }
  | ';'
      { $$ = NULL; }
  ;


type
  : INT_T
      { $$ = ast_allocate(TYPE_NODE, INT_T, 0); }
  | IVEC_T
      { $$ = ast_allocate(TYPE_NODE, IVEC_T, $1); }
  | BOOL_T
      {  $$ = ast_allocate(TYPE_NODE, BOOL_T, 0); }
  | BVEC_T
      { $$ = ast_allocate(TYPE_NODE, BVEC_T, $1); }
  | FLOAT_T
      { $$ = ast_allocate(TYPE_NODE, FLOAT_T, 0); }
  | VEC_T
      { $$ = ast_allocate(TYPE_NODE, VEC_T, $1); }
  ;


expression
  : type '(' arguments_opt ')' %prec '('
      { $$ = ast_allocate(CONSTRUCTOR_NODE, $1, $3); }
  | FUNC '(' arguments_opt ')' %prec '('
      { $$ = ast_allocate(FUNCTION_NODE, $1, $3); }
  | '-' expression %prec UMINUS
      { $$ = ast_allocate(UNARY_EXPR_NODE, '-', $2); }
  | '!' expression %prec '!'
      { $$ = ast_allocate(UNARY_EXPR_NODE, '!', $2); }
  | expression AND expression %prec AND
      { $$ = ast_allocate(BINARY_EXPR_NODE, AND, $1, $3); }
  | expression OR expression %prec OR
      { $$ = ast_allocate(BINARY_EXPR_NODE, OR, $1, $3); }
  | expression EQ expression %prec EQ
      { $$ = ast_allocate(BINARY_EXPR_NODE, EQ, $1, $3); }
  | expression NEQ expression %prec NEQ
      {  $$ = ast_allocate(BINARY_EXPR_NODE, NEQ, $1, $3); }
  | expression '<' expression %prec '<'
      { $$ = ast_allocate(BINARY_EXPR_NODE, '<', $1, $3); }
  | expression LEQ expression %prec LEQ
      { $$ = ast_allocate(BINARY_EXPR_NODE, LEQ, $1, $3); }
  | expression '>' expression %prec '>'
      { $$ = ast_allocate(BINARY_EXPR_NODE, '>', $1, $3); }
  | expression GEQ expression %prec GEQ
      { $$ = ast_allocate(BINARY_EXPR_NODE, GEQ, $1, $3); }
  | expression '+' expression %prec '+'
      { $$ = ast_allocate(BINARY_EXPR_NODE, '+', $1, $3); }
  | expression '-' expression %prec '-'
      { $$ = ast_allocate(BINARY_EXPR_NODE, '-', $1, $3); }
  | expression '*' expression %prec '*'
      { $$ = ast_allocate(BINARY_EXPR_NODE, '*', $1, $3); }
  | expression '/' expression %prec '/'
      { $$ = ast_allocate(BINARY_EXPR_NODE, '/', $1, $3); }
  | expression '^' expression %prec '^'
      { $$ = ast_allocate(BINARY_EXPR_NODE, '^', $1, $3); }
  | TRUE_C
      { $$ = ast_allocate(BOOL_LITERAL_NODE, 1); }
  | FALSE_C
      { $$ = ast_allocate(BOOL_LITERAL_NODE, 0); }
  | INT_C
      { $$ = ast_allocate(INT_LITERAL_NODE, $1); }
  | FLOAT_C
      { $$ = ast_allocate(FLOAT_LITERAL_NODE, $1); }
  | '(' expression ')'
      { $$ = $2; }
  | variable
      { $$ = $1; }
  ;

variable
  : ID
      { $$ = ast_allocate(VAR_NODE, $1, 0); }
  | ID '[' INT_C ']' %prec '['
      { $$ = ast_allocate(VAR_NODE, $1, 1, $3); }
  ;

arguments
  : arguments ',' expression
      { $$ = ast_allocate(ARGUMENTS_NODE, $3, $1); }
  | expression
      { $$ = ast_allocate(ARGUMENTS_NODE, $1, NULL); }
  ;

arguments_opt
  : arguments
      { $$ = $1; }
  |
      { $$ = NULL; }
  ;

%%

void yyerror(const char *message) {
    if (errorOccurred) return;
    errorOccurred = 1;
    fprintf(errorFile, "\nPARSER ERROR, LINE %d: %s\n", yyline, message);
}
