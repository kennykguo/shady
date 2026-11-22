// check names and types before code generation.
#include "semantic.h"
#include "symbol.h"
#include "parser.tab.h"
#include <stdlib.h>
#include "common.h"
#include <string.h>
#include <stdio.h>

static symbol_table *current_scope = NULL;
static int error_count = 0;

static int check_node(node *ast);
static void check_declaration(node *decl);
static int check_statement(node *stmt);
static int check_expression(node *expr);
static int get_expression_type(node *expr, int *vec_size);
static int types_match(int type1, int size1, int type2, int size2);
static int get_base_type(int type_code);
static int is_arithmetic_type(int type_code);
static int count_arguments(node *args);

// add a built-in variable to the outer scope.
static void add_predefined(char *name, int type, int vec_size, int is_const, int write_only,
                           int read_only) {
    symbol_entry *entry = (symbol_entry *)malloc(sizeof(symbol_entry));
    entry->name = strdup(name);
    entry->type_code = type;
    entry->vec_size = vec_size;
    entry->is_const = is_const;
    entry->is_write_only = write_only;
    entry->is_read_only = read_only;
    symbol_table_insert(current_scope, entry);
}

int semantic_check(node *ast) {
    error_count = 0;
    current_scope = symbol_table_create(NULL);

    // add the fragment output and position input.
    add_predefined("gl_FragColor", VEC_T, 3, 0, 1, 0);
    add_predefined("gl_FragCoord", VEC_T, 3, 0, 0, 1);

    // add the color and texture coordinate inputs.
    add_predefined("gl_TexCoord", VEC_T, 3, 0, 0, 1);
    add_predefined("gl_Color", VEC_T, 3, 0, 0, 1);

    check_node(ast);

    symbol_table_free(current_scope);
    return error_count;
}

// check declaration values in the saved list order.
static void process_declarations_in_order(node *decls) {
    if (!decls)
        return;
    // visit the end of the list first.
    process_declarations_in_order(decls->list.next);
    // check this declaration after the remaining list.
    check_declaration(decls->list.item);
}

static void process_statements_in_order(node *stmts) {
    if (!stmts)
        return;
    process_statements_in_order(stmts->list.next);
    check_statement(stmts->list.item);
}

static int check_node(node *ast) {
    if (!ast)
        return 0;

    switch (ast->kind) {
    case SCOPE_NODE: {
        // keep the parent scope so outer names remain available.
        symbol_table *new_scope = symbol_table_create(current_scope);
        symbol_table *old_scope = current_scope;
        current_scope = new_scope;

        // add all names before checking their initial values.
        node *curr_decl = ast->scope.declarations;
        while (curr_decl) {
            node *decl = curr_decl->list.item;
            if (decl && decl->kind == DECLARATION_NODE) {
                symbol_entry *entry = (symbol_entry *)malloc(sizeof(symbol_entry));
                entry->name = strdup(decl->declaration.identifier);
                entry->type_code = decl->declaration.type->type.type_code;
                entry->vec_size = decl->declaration.type->type.vec_size;
                entry->is_const = decl->declaration.is_const;
                entry->is_write_only = 0;
                entry->is_read_only = 0;

                if (!symbol_table_insert(current_scope, entry)) {
                    fprintf(errorFile, "error - variable '%s' already declared in this scope\n",
                            entry->name);
                    error_count++;
                    errorOccurred = 1;
                    free(entry->name);
                    free(entry);
                }
            }
            curr_decl = curr_decl->list.next;
        }

        // check initial values after all names are available.
        process_declarations_in_order(ast->scope.declarations);

        // check the statements in this scope.
        process_statements_in_order(ast->scope.statements);

        // release local names and restore the enclosing scope.
        symbol_table_free(current_scope);
        current_scope = old_scope;
        break;
    }
    default:
        break;
    }

    return 0;
}

static void check_declaration(node *decl) {
    if (!decl)
        return;

    // find the saved name before checking its initial value.
    symbol_entry *entry = symbol_table_lookup(current_scope, decl->declaration.identifier);
    if (!entry)
        return; // the missing entry was already reported.

    // check the initial value if one is present.
    if (decl->declaration.initializer) {
        int expr_type, expr_size;
        if (check_expression(decl->declaration.initializer)) {
            expr_type = get_expression_type(decl->declaration.initializer, &expr_size);

            // require matching types.
            if (!types_match(entry->type_code, entry->vec_size, expr_type, expr_size)) {
                fprintf(errorFile, "error - type mismatch in initialization of '%s'\n",
                        entry->name);
                error_count++;
                errorOccurred = 1;
            }

            // check the rules for constant initial values.
            if (entry->is_const) {
                // require a literal or a permitted constant input.
                if (decl->declaration.initializer->kind != INT_LITERAL_NODE &&
                    decl->declaration.initializer->kind != FLOAT_LITERAL_NODE &&
                    decl->declaration.initializer->kind != BOOL_LITERAL_NODE) {
                    // check if the referenced variable is constant.
                    if (decl->declaration.initializer->kind == VAR_NODE) {
                        symbol_entry *var = symbol_table_lookup(
                            current_scope, decl->declaration.initializer->variable.identifier);
                        if (!var || !var->is_const || !var->is_read_only) {
                            fprintf(errorFile,
                                    "error - const variable '%s' must be initialized with literal "
                                    "or uniform\n",
                                    entry->name);
                            error_count++;
                            errorOccurred = 1;
                        }
                    } else {
                        fprintf(errorFile,
                                "error - const variable '%s' must be initialized with literal or "
                                "uniform\n",
                                entry->name);
                        error_count++;
                        errorOccurred = 1;
                    }
                }
            }
        }
    }
}

static int check_statement(node *stmt) {
    if (!stmt)
        return 0;

    switch (stmt->kind) {
    case DECLARATION_NODE:
        // check a declaration found among statements.
        check_declaration(stmt);
        break;

    case ASSIGNMENT_NODE: {
        // require a declared variable.
        char *var_name = stmt->assignment.variable->variable.identifier;
        symbol_entry *var = symbol_table_lookup(current_scope, var_name);

        if (!var) {
            fprintf(errorFile, "error - undeclared variable '%s'\n", var_name);
            error_count++;
            errorOccurred = 1;
            return 1;
        }

        // reject assignments to constants.
        if (var->is_const) {
            fprintf(errorFile, "error - cannot assign to const variable '%s'\n", var_name);
            error_count++;
            errorOccurred = 1;
            return 1;
        }

        // reject assignments to input variables.
        if (var->is_read_only) {
            fprintf(errorFile, "error - cannot assign to read-only variable '%s'\n", var_name);
            error_count++;
            errorOccurred = 1;
            return 1;
        }

        // check the component index if one is present.
        if (stmt->assignment.variable->variable.is_array) {
            int elements = var->vec_size + 1; // the stored size is the component count minus one.
            int idx = stmt->assignment.variable->variable.array_index;

            if (idx < 0 || idx >= elements) {
                fprintf(errorFile, "error - array index %d out of bounds for variable '%s'\n", idx,
                        var_name);
                error_count++;
                errorOccurred = 1;
                return 1;
            }
        }

        // check the value expression. output variables cannot be read.
        // the expression checker enforces this restriction.
        if (!check_expression(stmt->assignment.expr)) {
            return 1;
        }

        // find the types of the target and the assigned value.
        int lhs_type, lhs_size;
        int rhs_type, rhs_size;

        lhs_type = get_expression_type(stmt->assignment.variable, &lhs_size);
        rhs_type = get_expression_type(stmt->assignment.expr, &rhs_size);

        if (!types_match(lhs_type, lhs_size, rhs_type, rhs_size)) {
            fprintf(errorFile, "error - type mismatch in assignment to '%s'\n", var_name);
            error_count++;
            errorOccurred = 1;
        }

        break;
    }

    case IF_STMT_NODE:
        // require a scalar boolean condition.
        if (check_expression(stmt->if_stmt.condition)) {
            int cond_type, cond_size;
            cond_type = get_expression_type(stmt->if_stmt.condition, &cond_size);
            if (cond_type != BOOL_T || cond_size != 0) {
                fprintf(errorFile, "error - if condition must be bool type\n");
                error_count++;
                errorOccurred = 1;
            }
        }
        check_statement(stmt->if_stmt.then_stmt);
        check_statement(stmt->if_stmt.else_stmt);
        break;

    case SCOPE_NODE:
        check_node(stmt);
        break;

    default:
        break;
    }

    return 0;
}

static int check_expression(node *expr) {
    if (!expr)
        return 0;

    switch (expr->kind) {
    case VAR_NODE: {
        symbol_entry *var = symbol_table_lookup(current_scope, expr->variable.identifier);
        if (!var) {
            fprintf(errorFile, "error - undeclared variable '%s'\n", expr->variable.identifier);
            error_count++;
            errorOccurred = 1;
            return 0;
        }

        if (var->is_write_only) {
            fprintf(errorFile, "error - cannot read from write-only variable '%s'\n",
                    expr->variable.identifier);
            error_count++;
            errorOccurred = 1;
            return 0;
        }

        if (expr->variable.is_array) {
            int elements = var->vec_size + 1; // the stored size is the component count minus one.
            if (expr->variable.array_index < 0 || expr->variable.array_index >= elements) {
                fprintf(errorFile, "error - array index %d out of bounds for variable '%s'\n",
                        expr->variable.array_index, expr->variable.identifier);
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        }

        // save the checked type on the expression node.
        expr->result_type = get_expression_type(expr, &(expr->result_vec_size));
        return 1;
    }

    case BINARY_EXPR_NODE: {
        if (!check_expression(expr->binary_expr.left) ||
            !check_expression(expr->binary_expr.right)) {
            return 0;
        }

        int left_type, left_size, right_type, right_size;
        left_type = get_expression_type(expr->binary_expr.left, &left_size);
        right_type = get_expression_type(expr->binary_expr.right, &right_size);

        int op = expr->binary_expr.op;

        if (op == AND || op == OR) {
            if (left_type != BOOL_T || right_type != BOOL_T) {
                fprintf(errorFile, "error - logical operators require bool operands\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            if (left_size != right_size) {
                fprintf(errorFile, "error - vector sizes must match for logical operators\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        } else if (op == '<' || op == LEQ || op == '>' || op == GEQ) {
            if (!is_arithmetic_type(left_type) || !is_arithmetic_type(right_type)) {
                fprintf(errorFile, "error - comparison operators require arithmetic types\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            if (left_size != 0 || right_size != 0) {
                fprintf(errorFile, "error - comparison operators only work on scalars\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            if (get_base_type(left_type) != get_base_type(right_type)) {
                fprintf(errorFile, "error - comparison operand types must match\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        } else if (op == EQ || op == NEQ) {
            if (get_base_type(left_type) != get_base_type(right_type)) {
                fprintf(errorFile, "error - equality operand types must match\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            if (left_size != right_size) {
                fprintf(errorFile, "error - vector sizes must match\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        } else if (op == '+' || op == '-' || op == '*' || op == '/' || op == '^') {
            if (!is_arithmetic_type(left_type) || !is_arithmetic_type(right_type)) {
                fprintf(errorFile, "error - arithmetic operators require arithmetic types\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            if (get_base_type(left_type) != get_base_type(right_type)) {
                fprintf(errorFile, "error - operand base types must match\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            if (op == '*') {
                if (!(left_size == right_size || left_size == 0 || right_size == 0)) {
                    fprintf(errorFile, "error - invalid vector sizes for multiplication\n");
                    error_count++;
                    errorOccurred = 1;
                    return 0;
                }
            } else if (op == '/' || op == '^') {
                if (left_size != 0 || right_size != 0) {
                    fprintf(errorFile, "error - division and power only work on scalars\n");
                    error_count++;
                    errorOccurred = 1;
                    return 0;
                }
            } else {
                if (left_size != right_size) {
                    fprintf(errorFile, "error - vector sizes must match\n");
                    error_count++;
                    errorOccurred = 1;
                    return 0;
                }
            }
        }

        // save the checked type on the expression node.
        expr->result_type = get_expression_type(expr, &(expr->result_vec_size));
        return 1;
    }

    case UNARY_EXPR_NODE: {
        if (!check_expression(expr->unary_expr.operand)) {
            return 0;
        }
        int operand_type, operand_size;
        operand_type = get_expression_type(expr->unary_expr.operand, &operand_size);

        if (expr->unary_expr.op == '!') {
            if (operand_type != BOOL_T) {
                fprintf(errorFile, "error - logical NOT requires bool operand\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        } else if (expr->unary_expr.op == '-') {
            if (!is_arithmetic_type(operand_type)) {
                fprintf(errorFile, "error - unary minus requires arithmetic type\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        }
        // save the checked type on the expression node.
        expr->result_type = get_expression_type(expr, &(expr->result_vec_size));
        return 1;
    }

    case INT_LITERAL_NODE:
        // save the checked type on the expression node.
        expr->result_type = INT_T;
        expr->result_vec_size = 0;
        return 1;

    case FLOAT_LITERAL_NODE:
        // save the checked type on the expression node.
        expr->result_type = FLOAT_T;
        expr->result_vec_size = 0;
        return 1;

    case BOOL_LITERAL_NODE:
        // save the checked type on the expression node.
        expr->result_type = BOOL_T;
        expr->result_vec_size = 0;
        return 1;

    case CONSTRUCTOR_NODE: {
        int cons_type = expr->constructor.type->type.type_code;
        int cons_size = expr->constructor.type->type.vec_size;
        int arg_count = count_arguments(expr->constructor.arguments);

        if (cons_size == 0) {
            if (arg_count != 1) {
                fprintf(errorFile, "error - scalar constructor needs 1 argument\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            node *arg = expr->constructor.arguments->list.item;
            check_expression(arg);
            int arg_type, arg_size;
            arg_type = get_expression_type(arg, &arg_size);
            if (!types_match(cons_type, 0, arg_type, arg_size)) {
                fprintf(errorFile, "error - constructor argument type mismatch\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        } else {
            int expected_args = cons_size + 1; // require one argument for each vector component.
            if (arg_count != expected_args) {
                fprintf(errorFile, "error - vector constructor needs %d arguments\n",
                        expected_args);
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            node *arg_node = expr->constructor.arguments;
            while (arg_node) {
                node *arg = arg_node->list.item;
                check_expression(arg);
                int arg_type, arg_size;
                arg_type = get_expression_type(arg, &arg_size);
                if (get_base_type(arg_type) != get_base_type(cons_type) || arg_size != 0) {
                    fprintf(errorFile, "error - constructor argument type mismatch\n");
                    error_count++;
                    errorOccurred = 1;
                    return 0;
                }
                arg_node = arg_node->list.next;
            }
        }
        // save the checked type on the expression node.
        expr->result_type = get_expression_type(expr, &(expr->result_vec_size));
        return 1;
    }

    case FUNCTION_NODE: {
        int func_id = expr->function.func_id;
        int arg_count = count_arguments(expr->function.arguments);

        if (func_id == DP3) {
            if (arg_count != 2) {
                fprintf(errorFile, "error - dp3 requires 2 arguments\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            node *arg1 = expr->function.arguments->list.item;
            node *arg2 = expr->function.arguments->list.next->list.item;
            check_expression(arg1);
            check_expression(arg2);
            int type1, size1, type2, size2;
            type1 = get_expression_type(arg1, &size1);
            type2 = get_expression_type(arg2, &size2);

            // the stored size is the component count minus one.
            if (!((size1 == 2 || size1 == 3) && (size2 == 2 || size2 == 3))) {
                fprintf(errorFile, "error - dp3 requires vec3/vec4 or ivec3/ivec4 arguments\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            if (!types_match(type1, size1, type2, size2)) {
                fprintf(errorFile, "error - dp3 arguments must have same type\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        } else if (func_id == RSQ || (func_id >= SIN && func_id <= ABS)) {
            if (arg_count != 1) {
                fprintf(errorFile, "error - scalar math function requires 1 argument\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            node *arg = expr->function.arguments->list.item;
            check_expression(arg);
            int arg_type, arg_size;
            arg_type = get_expression_type(arg, &arg_size);
            if (!(arg_size == 0 &&
                  (arg_type == FLOAT_T || (func_id == RSQ && arg_type == INT_T)))) {
                fprintf(errorFile,
                        "error - math function requires a float scalar (rsq also accepts int)\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        } else if (func_id == LIT) {
            if (arg_count != 1) {
                fprintf(errorFile, "error - lit requires 1 argument\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
            node *arg = expr->function.arguments->list.item;
            check_expression(arg);
            int arg_type, arg_size;
            arg_type = get_expression_type(arg, &arg_size);
            if (arg_type != VEC_T ||
                arg_size != 3) { // require a four component floating point vector.
                fprintf(errorFile, "error - lit requires vec4 argument\n");
                error_count++;
                errorOccurred = 1;
                return 0;
            }
        }
        // save the checked type on the expression node.
        expr->result_type = get_expression_type(expr, &(expr->result_vec_size));
        return 1;
    }

    default:
        return 1;
    }
}

static int get_expression_type(node *expr, int *vec_size) {
    *vec_size = 0;

    if (!expr)
        return -1;

    switch (expr->kind) {
    case INT_LITERAL_NODE:
        return INT_T;
    case FLOAT_LITERAL_NODE:
        return FLOAT_T;
    case BOOL_LITERAL_NODE:
        return BOOL_T;

    case VAR_NODE: {
        symbol_entry *var = symbol_table_lookup(current_scope, expr->variable.identifier);
        if (var) {
            if (expr->variable.is_array) {
                // a vector component has the scalar base type.
                *vec_size = 0;
                return get_base_type(var->type_code); // return the scalar base type.
            } else {
                *vec_size = var->vec_size;
                return var->type_code;
            }
        }
        return -1;
    }

    case BINARY_EXPR_NODE: {
        int left_type, left_size;
        left_type = get_expression_type(expr->binary_expr.left, &left_size);

        int op = expr->binary_expr.op;

        // comparisons and logical operations return a boolean type.
        if (op == '<' || op == LEQ || op == '>' || op == GEQ || op == EQ || op == NEQ ||
            op == AND || op == OR) {
            *vec_size = left_size; // keep the vector size for logical operations.
            return BOOL_T;
        }

        // arithmetic uses the operand type.
        // multiplication with a vector has a vector result type.
        if (op == '*') {
            int right_type, right_size;
            right_type = get_expression_type(expr->binary_expr.right, &right_size);
            *vec_size = (left_size > right_size) ? left_size : right_size;
            // use the vector type when the sizes differ.
            if (left_size > right_size) {
                return left_type; // use the left vector type.
            } else if (right_size > left_size) {
                return right_type; // use the right vector type.
            } else {
                return left_type; // use the shared operand type.
            }
        }

        *vec_size = left_size;
        return left_type;
    }

    case UNARY_EXPR_NODE:
        return get_expression_type(expr->unary_expr.operand, vec_size);

    case CONSTRUCTOR_NODE:
        *vec_size = expr->constructor.type->type.vec_size;
        return expr->constructor.type->type.type_code;

    case FUNCTION_NODE: {
        int func_id = expr->function.func_id;
        if (func_id == DP3) {
            // use the scalar type of the argument.
            node *arg = expr->function.arguments->list.item;
            int arg_type, arg_size;
            arg_type = get_expression_type(arg, &arg_size);
            *vec_size = 0;
            return (arg_type == IVEC_T) ? INT_T : FLOAT_T;
        } else if (func_id == RSQ || (func_id >= SIN && func_id <= ABS)) {
            *vec_size = 0;
            return FLOAT_T;
        } else if (func_id == LIT) {
            *vec_size = 3;
            return VEC_T;
        }
        return -1;
    }

    default:
        return -1;
    }
}

static int types_match(int type1, int size1, int type2, int size2) {
    return (type1 == type2 && size1 == size2);
}

static int get_base_type(int type_code) {
    switch (type_code) {
    case INT_T:
    case IVEC_T:
        return INT_T;
    case FLOAT_T:
    case VEC_T:
        return FLOAT_T;
    case BOOL_T:
    case BVEC_T:
        return BOOL_T;
    default:
        return type_code;
    }
}

static int is_arithmetic_type(int type_code) {
    return (type_code == INT_T || type_code == FLOAT_T || type_code == IVEC_T ||
            type_code == VEC_T);
}

static int count_arguments(node *args) {
    int count = 0;
    while (args) {
        count++;
        args = args->list.next;
    }
    return count;
}
