#ifndef CODEGEN_H
#define CODEGEN_H

#include "ast.h"
#include <stdio.h>

// write the checked syntax tree as assembly.
void generate_code(node *ast, FILE *output);

#endif