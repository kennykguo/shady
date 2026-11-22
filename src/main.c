/* parse and check a shader before writing assembly. */
#include "common.h"
#include "ast.h"
#include "semantic.h"
#include "codegen.h"
#include <stdlib.h>
#include <string.h>

extern int yyparse(void);

static void usage(FILE *out) {
    fprintf(out, "usage: shady [--ast] [-o output.spvasm] [source.frag]\n"
                 "Reads stdin when no source file is supplied.\n");
}

int main(int argc, char **argv) {
    const char *source = NULL;
    const char *destination = NULL;
    int show_ast = 0;
    inputFile = stdin;
    FILE *outputFile = stdout;
    errorFile = stderr;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-h")) {
            usage(stdout);
            return EXIT_SUCCESS;
        } else if (!strcmp(argv[i], "--ast") || !strcmp(argv[i], "-Da")) {
            show_ast = 1;
        } else if (!strcmp(argv[i], "-o")) {
            if (++i == argc) {
                usage(stderr);
                return EXIT_FAILURE;
            }
            destination = argv[i];
        } else if (argv[i][0] == '-' || source) {
            usage(stderr);
            return EXIT_FAILURE;
        } else {
            source = argv[i];
        }
    }
    if (source && !(inputFile = fopen(source, "r"))) {
        perror(source);
        return EXIT_FAILURE;
    }
    // stop before code generation if parsing or type checks fail.
    int status = yyparse();
    if (!status && !errorOccurred)
        status = semantic_check(ast);
    if (!status && !errorOccurred) {
        if (show_ast) {
            ast_print(ast);
        } else {
            if (destination && !(outputFile = fopen(destination, "w"))) {
                perror(destination);
                status = 1;
            } else {
                generate_code(ast, outputFile);
            }
        }
    }
    ast_free(ast);
    if (inputFile != stdin)
        fclose(inputFile);
    if (outputFile != stdout && outputFile && fclose(outputFile))
        status = 1;
    if (ferror(stdout))
        status = 1;
    return status || errorOccurred ? EXIT_FAILURE : EXIT_SUCCESS;
}
