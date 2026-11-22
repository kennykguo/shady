
#ifndef AST_H_
#define AST_H_ 1

#include <stdarg.h>

enum { DP3 = 0, LIT = 1, RSQ = 2, SIN, COS, FRACT, ABS };

// the node kind selects the fields used in the union.

// declare the node type before use.
struct node_;
typedef struct node_ node;
extern node *ast;

typedef enum {
    UNKNOWN = 0,

    // these node kinds describe expressions.
    BINARY_EXPR_NODE,
    UNARY_EXPR_NODE,
    BOOL_LITERAL_NODE,
    INT_LITERAL_NODE,
    FLOAT_LITERAL_NODE,
    VAR_NODE,         // read a variable or a vector component.
    FUNCTION_NODE,    // call a built-in function.
    CONSTRUCTOR_NODE, // construct a value of the requested type.

    // these node kinds describe statements.
    ASSIGNMENT_NODE,
    IF_STMT_NODE,
    SCOPE_NODE,

    // these node kinds describe declarations.
    DECLARATION_NODE,
    DECLARATIONS_NODE, // store a list of declarations.

    // store a list of statements.
    STATEMENTS_NODE,

    // store a declared type.
    TYPE_NODE,

    // store a list of arguments.
    ARGUMENTS_NODE
} node_kind;

struct node_ {
    node_kind kind;

    int result_type;     // the type from the parser.
    int result_vec_size; // zero means scalar. vector sizes are the component count minus one.

    union {
        // store the operator and its two operands.
        struct {
            int op;
            node *left;
            node *right;
        } binary_expr;

        // store the operator and its operand.
        struct {
            int op;
            node *operand;
        } unary_expr;

        // store literal values.
        struct {
            int value;
        } int_literal;

        struct {
            float value;
        } float_literal;

        struct {
            int value; // zero means false. one means true.
        } bool_literal;

        // store a variable name and an optional component index.
        struct {
            char *identifier;
            int is_array;    // set when a vector component is selected.
            int array_index; // use this index only when a component is selected.
        } variable;

        // store a built-in function call.
        struct {
            int func_id;     // identify the built-in function.
            node *arguments; // point to the argument list.
        } function;

        // store the type and constructor arguments.
        struct {
            node *type;      // point to the type node.
            node *arguments; // point to the argument list.
        } constructor;

        // store the assignment target and value.
        struct {
            node *variable; // point to the variable node.
            node *expr;     // point to the expression node.
        } assignment;

        // store a condition and its branches.
        struct {
            node *condition; // point to the expression node.
            node *then_stmt; // point to the statement node.
            node *else_stmt; // point to the false branch if one is present.
        } if_stmt;

        // store the declarations and statements for one scope.
        struct {
            node *declarations; // point to the declaration list.
            node *statements;   // point to the statement list.
        } scope;

        // store a name and type with an optional initial value.
        struct {
            int is_const;
            node *type; // point to the type node.
            char *identifier;
            node *initializer; // point to the initial value if one is present.
        } declaration;

        // store the type and vector size.
        struct {
            int type_code; // use the type code from the parser.
            int vec_size;  // zero means scalar. vector sizes are the component count minus one.
        } type;

        // connect nodes in a list.
        struct {
            node *item; // point to the list item.
            node *next; // point to the next item if one is present.
        } list;
    };
};

node *ast_allocate(node_kind type, ...);
void ast_free(node *ast);
void ast_print(node *ast);

#endif /* end the syntax tree header. */
