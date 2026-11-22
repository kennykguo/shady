#include "codegen.h"
#include "ast.h"
#include "parser.tab.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void gen_statement(node *stmt, FILE *out, int predicate_id);
static int gen_expression(node *expr, FILE *out);

static int next_id = 100;

// save constants so they can be written before the function.
typedef struct const_entry {
    char *text; // the complete constant instruction.
    struct const_entry *next;
} const_entry;

static const_entry *const_pool = NULL;

static void add_const(const char *text) {
    const_entry *e = (const_entry *)malloc(sizeof(const_entry));
    e->text = strdup(text);
    e->next = const_pool;
    const_pool = e;
}

static void emit_constants(FILE *out) {
    // reverse the list to restore the order of declarations.
    const_entry *reversed = NULL;
    while (const_pool) {
        const_entry *temp = const_pool;
        const_pool = const_pool->next;
        temp->next = reversed;
        reversed = temp;
    }

    // write each constant and release its memory.
    while (reversed) {
        fprintf(out, "%s", reversed->text);
        const_entry *temp = reversed;
        reversed = reversed->next;
        free(temp->text);
        free(temp);
    }
    const_pool = NULL;
}

typedef struct var_entry {
    char *name;
    int id;
    int type_code; // the type from the parser.
    int vec_size;  // zero means scalar. vector sizes are the component count minus one.
    struct var_entry *next;
} var_entry;

static var_entry *local_vars = NULL;

// declare functions before use.
static void add_local_var(const char *name, int id, int type_code, int vec_size);
static int lookup_var(const char *name);
static const char *lookup_var_type(const char *name);
static void clear_local_vars(void);
static int gen_id(void);
static const char *get_spirv_type(int type_code, int vec_size);
static const char *get_builtin_var(const char *name);

// save the name and type of a local variable.
static void add_local_var(const char *name, int id, int type_code, int vec_size) {
    var_entry *e = (var_entry *)malloc(sizeof(var_entry));
    e->name = strdup(name);
    e->id = id;
    e->type_code = type_code;
    e->vec_size = vec_size;
    e->next = local_vars;
    local_vars = e;
}

// find the identifier used in the output instructions.
static int lookup_var(const char *name) {
    for (var_entry *e = local_vars; e; e = e->next) {
        if (strcmp(e->name, name) == 0) {
            return e->id;
        }
    }
    return -1;
}

// find the type used in the output instructions.
static const char *lookup_var_type(const char *name) {
    for (var_entry *e = local_vars; e; e = e->next) {
        if (strcmp(e->name, name) == 0) {
            return get_spirv_type(e->type_code, e->vec_size);
        }
    }
    return "%t_vec4"; // use the default type if the name is not found.
}

static int lookup_var_vec_size(const char *name) {
    for (var_entry *e = local_vars; e; e = e->next) {
        if (strcmp(e->name, name) == 0) {
            return e->vec_size;
        }
    }
    return 4; // use a four component vector if the name is not found.
}

// release the list of local variables.
static void clear_local_vars(void) {
    while (local_vars) {
        var_entry *temp = local_vars;
        local_vars = local_vars->next;
        free(temp->name);
        free(temp);
    }
}

static int gen_id(void) { return next_id++; }

// reserve storage for the variables in this scope.
static void process_decls_allocate(node *decls, FILE *out) {
    if (!decls)
        return;
    process_decls_allocate(decls->list.next, out);

    node *decl = decls->list.item;

    // write a storage instruction for this variable.
    int type_code = decl->declaration.type->type.type_code;
    int vec_size = decl->declaration.type->type.vec_size;
    const char *spirv_type = get_spirv_type(type_code, vec_size);

    int var_id = gen_id();
    fprintf(out, "%%%-3d = OpVariable %%t_ptr_func_%s Function\n", var_id,
            spirv_type + 3); // skip the common type prefix.

    // save the variable name and its type.
    add_local_var(decl->declaration.identifier, var_id, type_code, vec_size);
}

// write the initial values after storage is reserved.
static void process_decls_initialize(node *decls, FILE *out) {
    if (!decls)
        return;

    node *decl = decls->list.item;

    // evaluate the initial value if one is present.
    if (decl->declaration.initializer) {
        int var_id = lookup_var(decl->declaration.identifier);
        int init_id = gen_expression(decl->declaration.initializer, out);
        fprintf(out, "OpStore %%%-3d %%%-3d\n", var_id, init_id);
    }

    process_decls_initialize(decls->list.next, out);
}

// process statements in source order.
static void process_stmts_codegen(node *stmts, FILE *out, int predicate_id) {
    if (!stmts)
        return;
    gen_statement(stmts->list.item, out, predicate_id);
    process_stmts_codegen(stmts->list.next, out, predicate_id);
}

static void emit_prologue(FILE *out) {
    fprintf(out, "; ===== miniglsl fragment shader prologue =====\n");
    fprintf(out, "OpCapability Shader\n");
    fprintf(out, "%%ext = OpExtInstImport \"GLSL.std.450\"\n");
    fprintf(out, "OpMemoryModel Logical GLSL450\n");
    fprintf(out, "OpEntryPoint Fragment %%main \"main\" %%mglsl_Color %%gl_FragCoord "
                 "%%mglsl_FragColor %%mglsl_TexCoord\n");
    fprintf(out, "OpExecutionMode %%main OriginUpperLeft\n\n");
    fprintf(out, "; ---- decorations ----\n");
    fprintf(out, "OpDecorate %%gl_FragCoord BuiltIn FragCoord\n");
    fprintf(out, "OpDecorate %%mglsl_Color Location 0\n");
    fprintf(out, "OpDecorate %%mglsl_FragColor Location 0\n");
    fprintf(out, "OpDecorate %%mglsl_TexCoord Location 1\n");
    fprintf(out, "; ---- types ----\n");
    fprintf(out, "%%t_void = OpTypeVoid\n");
    fprintf(out, "%%t_fn = OpTypeFunction %%t_void\n");
    fprintf(out, "%%t_float = OpTypeFloat 32\n");
    fprintf(out, "%%t_bool = OpTypeBool\n");
    fprintf(out, "%%t_int = OpTypeInt 32 1\n");
    fprintf(out, "%%t_vec2 = OpTypeVector %%t_float 2\n");
    fprintf(out, "%%t_vec3 = OpTypeVector %%t_float 3\n");
    fprintf(out, "%%t_vec4 = OpTypeVector %%t_float 4\n");
    fprintf(out, "%%t_bvec2 = OpTypeVector %%t_bool 2\n");
    fprintf(out, "%%t_bvec3 = OpTypeVector %%t_bool 3\n");
    fprintf(out, "%%t_bvec4 = OpTypeVector %%t_bool 4\n\n");
    fprintf(out, "; ---- pointer types ----\n");
    fprintf(out, "%%t_ptr_input_vec4 = OpTypePointer Input %%t_vec4\n");
    fprintf(out, "%%t_ptr_output_vec4 = OpTypePointer Output %%t_vec4\n");
    fprintf(out, "%%t_ptr_func_float = OpTypePointer Function %%t_float\n");
    fprintf(out, "%%t_ptr_func_vec2 = OpTypePointer Function %%t_vec2\n");
    fprintf(out, "%%t_ptr_func_vec3 = OpTypePointer Function %%t_vec3\n");
    fprintf(out, "%%t_ptr_func_vec4 = OpTypePointer Function %%t_vec4\n\n");
    fprintf(out, "; ---- interface variables ----\n");
    fprintf(out, "%%mglsl_Color = OpVariable %%t_ptr_input_vec4 Input\n");
    fprintf(out, "%%gl_FragCoord = OpVariable %%t_ptr_input_vec4 Input\n");
    fprintf(out, "%%mglsl_TexCoord = OpVariable %%t_ptr_input_vec4 Input\n");
    fprintf(out, "%%mglsl_FragColor = OpVariable %%t_ptr_output_vec4 Output\n\n");
    fprintf(out, "; ---- shared constants ----\n");
    fprintf(out, "%%c_float_0 = OpConstant %%t_float 0.0\n");
    fprintf(out, "%%c_float_1 = OpConstant %%t_float 1.0\n\n");
}

static const char *get_spirv_type(int type_code, int vec_size) {
    if (vec_size == 0) {
        switch (type_code) {
        case FLOAT_T:
            return "%t_float";
        case INT_T:
            return "%t_int";
        case BOOL_T:
            return "%t_bool";
        default:
            return "%t_float";
        }
    } else {
        switch (vec_size) {
        case 1:
            return "%t_vec2";
        case 2:
            return "%t_vec3";
        case 3:
            return "%t_vec4";
        default:
            return "%t_vec4";
        }
    }
}

static const char *get_builtin_var(const char *name) {
    if (strcmp(name, "gl_FragColor") == 0)
        return "%mglsl_FragColor";
    if (strcmp(name, "gl_Color") == 0)
        return "%mglsl_Color";
    if (strcmp(name, "gl_TexCoord") == 0)
        return "%mglsl_TexCoord";
    if (strcmp(name, "gl_FragCoord") == 0)
        return "%gl_FragCoord";
    return NULL;
}

// write instructions for an expression. return the result identifier.
static int gen_expression(node *expr, FILE *out) {
    if (!expr)
        return -1;

    switch (expr->kind) {
    case VAR_NODE: {
        // load a variable or one of its components.
        const char *builtin = get_builtin_var(expr->variable.identifier);
        if (builtin) {
            int result = gen_id();

            if (expr->variable.is_array) {
                // read one component of an input vector.
                // load the vector. then extract the requested component.
                int loaded = gen_id();
                fprintf(out, "%%%-3d = OpLoad %%t_vec4 %s\n", loaded, builtin);
                fprintf(out, "%%%-3d = OpCompositeExtract %%t_float %%%-3d %d\n", result, loaded,
                        expr->variable.array_index);
            } else {
                // load the complete value.
                fprintf(out, "%%%-3d = OpLoad %%t_vec4 %s\n", result, builtin);
            }
            return result;
        } else {
            // find the local variable in the saved list.
            int var_id = lookup_var(expr->variable.identifier);
            if (var_id < 0) {
                fprintf(stderr, "error - undefined variable %s\n", expr->variable.identifier);
                return -1;
            }

            const char *var_type = lookup_var_type(expr->variable.identifier);
            int result = gen_id();

            if (expr->variable.is_array) {
                // read one vector component.
                int loaded = gen_id();
                fprintf(out, "%%%-3d = OpLoad %s %%%-3d\n", loaded, var_type, var_id);
                fprintf(out, "%%%-3d = OpCompositeExtract %%t_float %%%-3d %d\n", result, loaded,
                        expr->variable.array_index);
            } else {
                // load the complete value.
                fprintf(out, "%%%-3d = OpLoad %s %%%-3d\n", result, var_type, var_id);
            }
            return result;
        }
    }

    case INT_LITERAL_NODE: {
        int const_id = gen_id();
        char buf[256];
        snprintf(buf, sizeof(buf), "%%%-3d = OpConstant %%t_int %d\n", const_id,
                 expr->int_literal.value);
        add_const(buf);
        return const_id;
    }

    case FLOAT_LITERAL_NODE: {
        int const_id = gen_id();
        char buf[256];
        snprintf(buf, sizeof(buf), "%%%-3d = OpConstant %%t_float %f\n", const_id,
                 expr->float_literal.value);
        add_const(buf);
        return const_id;
    }

    case BOOL_LITERAL_NODE: {
        int const_id = gen_id();
        char buf[256];
        if (expr->bool_literal.value) {
            snprintf(buf, sizeof(buf), "%%%-3d = OpConstantTrue %%t_bool\n", const_id);
        } else {
            snprintf(buf, sizeof(buf), "%%%-3d = OpConstantFalse %%t_bool\n", const_id);
        }
        add_const(buf);
        return const_id;
    }

    case UNARY_EXPR_NODE: {
        // evaluate the operand before this operation.
        int operand = gen_expression(expr->unary_expr.operand, out);
        if (operand < 0)
            return -1;

        int result = gen_id();
        const char *type = get_spirv_type(expr->result_type, expr->result_vec_size);

        switch (expr->unary_expr.op) {
        case '-':
            // change the sign of the value.
            fprintf(out, "%%%-3d = OpFNegate %s %%%-3d\n", result, type, operand);
            break;
        case '!':
            // invert the boolean value.
            fprintf(out, "%%%-3d = OpLogicalNot %%t_bool %%%-3d\n", result, operand);
            break;
        default:
            fprintf(stderr, "unimplemented unary op: %d\n", expr->unary_expr.op);
            return -1;
        }
        return result;
    }

    case BINARY_EXPR_NODE: {
        // evaluate both operands before the operation.
        int left = gen_expression(expr->binary_expr.left, out);
        int right = gen_expression(expr->binary_expr.right, out);
        if (left < 0 || right < 0)
            return -1;

        int result = gen_id();
        const char *type = get_spirv_type(expr->result_type, expr->result_vec_size);

        switch (expr->binary_expr.op) {
        // write the arithmetic instruction.
        case '+':
            fprintf(out, "%%%-3d = OpFAdd %s %%%-3d %%%-3d\n", result, type, left, right);
            break;
        case '-':
            fprintf(out, "%%%-3d = OpFSub %s %%%-3d %%%-3d\n", result, type, left, right);
            break;
        case '*':
            fprintf(out, "%%%-3d = OpFMul %s %%%-3d %%%-3d\n", result, type, left, right);
            break;
        case '/':
            fprintf(out, "%%%-3d = OpFDiv %s %%%-3d %%%-3d\n", result, type, left, right);
            break;

        // compare scalar values and return a boolean.
        case '<':
            fprintf(out, "%%%-3d = OpFOrdLessThan %%t_bool %%%-3d %%%-3d\n", result, left, right);
            break;
        case '>':
            fprintf(out, "%%%-3d = OpFOrdGreaterThan %%t_bool %%%-3d %%%-3d\n", result, left,
                    right);
            break;
        case EQ: // test if the values are equal.
            fprintf(out, "%%%-3d = OpFOrdEqual %%t_bool %%%-3d %%%-3d\n", result, left, right);
            break;
        case NEQ: // test if the values are not equal.
            fprintf(out, "%%%-3d = OpFOrdNotEqual %%t_bool %%%-3d %%%-3d\n", result, left, right);
            break;
        case LEQ: // test if the left value is less than or equal to the right value.
            fprintf(out, "%%%-3d = OpFOrdLessThanEqual %%t_bool %%%-3d %%%-3d\n", result, left,
                    right);
            break;
        case GEQ: // test if the left value is greater than or equal to the right value.
            fprintf(out, "%%%-3d = OpFOrdGreaterThanEqual %%t_bool %%%-3d %%%-3d\n", result, left,
                    right);
            break;

        // combine boolean values.
        case AND: // require both conditions to be true.
            fprintf(out, "%%%-3d = OpLogicalAnd %%t_bool %%%-3d %%%-3d\n", result, left, right);
            break;
        case OR: // require at least one condition to be true.
            fprintf(out, "%%%-3d = OpLogicalOr %%t_bool %%%-3d %%%-3d\n", result, left, right);
            break;

        default:
            fprintf(stderr, "unimplemented binary op: %d\n", expr->binary_expr.op);
            return -1;
        }
        return result;
    }

    case CONSTRUCTOR_NODE: {
        // collect the result identifiers from the argument list.
        int args[16]; // store at most sixteen argument identifiers.
        int num_args = 0;

        node *arg_list = expr->constructor.arguments;
        while (arg_list && num_args < 16) {
            int arg_id = gen_expression(arg_list->list.item, out);
            if (arg_id < 0)
                return -1;
            args[num_args++] = arg_id;
            arg_list = arg_list->list.next;
        }

        // reverse the arguments to restore source order.
        // the parser puts the last argument at the start of the list.
        // the collected arguments are in reverse order.
        // the output instruction needs the first argument first.
        for (int i = 0; i < num_args / 2; i++) {
            int temp = args[i];
            args[i] = args[num_args - 1 - i];
            args[num_args - 1 - i] = temp;
        }

        int result = gen_id();
        const char *type = get_spirv_type(expr->result_type, expr->result_vec_size);

        // combine the scalar arguments into a vector.
        fprintf(out, "%%%-3d = OpCompositeConstruct %s", result, type);
        for (int i = 0; i < num_args; i++) {
            fprintf(out, " %%%-3d", args[i]);
        }
        fprintf(out, "\n");

        return result;
    }

    case FUNCTION_NODE: {
        // select the extended instruction for this function.
        int func_id = expr->function.func_id;
        int inst_id = -1;
        static const char *math_names[] = {"Sin", "Cos", "Fract", "FAbs"};
        const char *math_name = NULL;

        if (func_id == DP3)
            inst_id = 16; // this is the current dot product mapping.
        else if (func_id == RSQ)
            inst_id = 32; // this is the inverse square root operation.
        else if (func_id == LIT)
            inst_id = 18; // this is the current lighting function mapping.
        else if (func_id >= SIN && func_id <= ABS)
            math_name = math_names[func_id - SIN];
        else {
            fprintf(stderr, "error - unknown function id %d\n", func_id);
            return -1;
        }

        // collect the results from the argument list.
        int args[4];
        int num_args = 0;
        node *arg_list = expr->function.arguments;
        while (arg_list && num_args < 4) {
            int arg_id = gen_expression(arg_list->list.item, out);
            if (arg_id < 0)
                return -1;
            args[num_args++] = arg_id;
            arg_list = arg_list->list.next;
        }

        // reverse the arguments to restore source order.
        for (int i = 0; i < num_args / 2; i++) {
            int temp = args[i];
            args[i] = args[num_args - 1 - i];
            args[num_args - 1 - i] = temp;
        }

        int result = gen_id();
        const char *type = get_spirv_type(expr->result_type, expr->result_vec_size);

        // write the extended instruction and its arguments.
        if (func_id == RSQ || math_name)
            fprintf(out, "%%%-3d = OpExtInst %s %%ext %s", result, type,
                    math_name ? math_name : "InverseSqrt");
        else
            fprintf(out, "%%%-3d = OpExtInst %s %%ext %d", result, type, inst_id);
        for (int i = 0; i < num_args; i++) {
            fprintf(out, " %%%-3d", args[i]);
        }
        fprintf(out, "\n");

        return result;
    }

    default:
        fprintf(stderr, "error - unimplemented expression kind %d\n", expr->kind);
        return -1;
    }
}

// write instructions for a statement.
static void gen_statement(node *stmt, FILE *out, int predicate_id) {
    if (!stmt)
        return;

    switch (stmt->kind) {
    case ASSIGNMENT_NODE: {
        // evaluate the value to assign.
        int rhs_id = gen_expression(stmt->assignment.expr, out);
        if (rhs_id < 0)
            return;

        // find the assignment target.
        const char *var_name = stmt->assignment.variable->variable.identifier;
        node *lhs_var = stmt->assignment.variable;
        const char *builtin = get_builtin_var(var_name);

        // check if the target is one vector component.
        if (lhs_var->variable.is_array) {
            int index = lhs_var->variable.array_index;

            // find the output identifier for the target.
            int var_id;
            if (builtin) {
                // input components cannot be changed.
                fprintf(stderr, "error - cannot assign to indexed builtin %s\n", var_name);
                return;
            } else {
                var_id = lookup_var(var_name);
                if (var_id < 0) {
                    fprintf(stderr, "error - undefined variable %s\n", var_name);
                    return;
                }
            }

            // load the current vector value.
            int loaded = gen_id();
            fprintf(out, "%%%-3d = OpLoad %%t_vec4 %%%-3d\n", loaded, var_id);

            // replace the requested component.
            int updated = gen_id();
            fprintf(out, "%%%-3d = OpCompositeInsert %%t_vec4 %%%-3d %%%-3d %d\n", updated, rhs_id,
                    loaded, index);

            // keep the new value only when the condition is true.
            if (predicate_id > 0) {
                // this path assumes four components. smaller vectors are not supported.
                int selected = gen_id();

                // copy the condition to each of the four components.
                int pred_vec = gen_id();
                fprintf(out,
                        "%%%-3d = OpCompositeConstruct %%t_bvec4 %%%-3d %%%-3d %%%-3d %%%-3d\n",
                        pred_vec, predicate_id, predicate_id, predicate_id, predicate_id);

                fprintf(out, "%%%-3d = OpSelect %%t_vec4 %%%-3d %%%-3d %%%-3d\n", selected,
                        pred_vec, updated, loaded);
                updated = selected;
            }

            // store the selected vector.
            fprintf(out, "OpStore %%%-3d %%%-3d\n", var_id, updated);
        } else {
            // assign a complete value.

            // load the old value so a false condition can keep it.
            if (predicate_id > 0) {
                int current_val_id;
                const char *type_str;
                int vec_size = 0;

                if (builtin) {
                    current_val_id = gen_id();
                    fprintf(out, "%%%-3d = OpLoad %%t_vec4 %s\n", current_val_id, builtin);
                    type_str = "%t_vec4";
                    vec_size = 4;
                } else {
                    int var_id = lookup_var(var_name);
                    if (var_id < 0) {
                        fprintf(stderr, "error - undefined variable %s\n", var_name);
                        return;
                    }
                    const char *var_type = lookup_var_type(var_name);
                    vec_size = lookup_var_vec_size(var_name);
                    current_val_id = gen_id();
                    fprintf(out, "%%%-3d = OpLoad %s %%%-3d\n", current_val_id, var_type, var_id);
                    type_str = var_type;
                }

                // choose the new value when the condition is true.
                int selected = gen_id();

                // use one boolean condition for each vector component.
                if (vec_size > 0) {
                    // copy the scalar condition into a boolean vector.
                    int pred_vec = gen_id();
                    if (vec_size == 1) { // use two components.
                        fprintf(out, "%%%-3d = OpCompositeConstruct %%t_bvec2 %%%-3d %%%-3d\n",
                                pred_vec, predicate_id, predicate_id);
                        fprintf(out, "%%%-3d = OpSelect %s %%%-3d %%%-3d %%%-3d\n", selected,
                                type_str, pred_vec, rhs_id, current_val_id);
                    } else if (vec_size == 2) { // use three components.
                        fprintf(out,
                                "%%%-3d = OpCompositeConstruct %%t_bvec3 %%%-3d %%%-3d %%%-3d\n",
                                pred_vec, predicate_id, predicate_id, predicate_id);
                        fprintf(out, "%%%-3d = OpSelect %s %%%-3d %%%-3d %%%-3d\n", selected,
                                type_str, pred_vec, rhs_id, current_val_id);
                    } else { // use the four component path.
                        fprintf(
                            out,
                            "%%%-3d = OpCompositeConstruct %%t_bvec4 %%%-3d %%%-3d %%%-3d %%%-3d\n",
                            pred_vec, predicate_id, predicate_id, predicate_id, predicate_id);
                        fprintf(out, "%%%-3d = OpSelect %s %%%-3d %%%-3d %%%-3d\n", selected,
                                type_str, pred_vec, rhs_id, current_val_id);
                    }
                } else {
                    // select between scalar values.
                    fprintf(out, "%%%-3d = OpSelect %s %%%-3d %%%-3d %%%-3d\n", selected, type_str,
                            predicate_id, rhs_id, current_val_id);
                }

                rhs_id = selected;
            }

            if (builtin) {
                // store the shader output.
                fprintf(out, "OpStore %s %%%-3d\n", builtin, rhs_id);
            } else {
                // store the local variable.
                int var_id = lookup_var(var_name);
                if (var_id < 0) {
                    fprintf(stderr, "error - undefined variable %s\n", var_name);
                    return;
                }
                fprintf(out, "OpStore %%%-3d %%%-3d\n", var_id, rhs_id);
            }
        }
        break;
    }

    case IF_STMT_NODE: {
        // evaluate both branches. use conditions to select which values are stored.
        // nested branches must also satisfy their outer conditions.
        int cond_id = gen_expression(stmt->if_stmt.condition, out);
        if (cond_id < 0)
            return;

        // find the condition for each branch.
        int then_pred = cond_id;
        int else_pred = -1;

        // require the outer condition and this condition to be true.
        if (predicate_id > 0) {
            int combined = gen_id();
            fprintf(out, "%%%-3d = OpLogicalAnd %%t_bool %%%-3d %%%-3d\n", combined, predicate_id,
                    cond_id);
            then_pred = combined;
        }

        // process the true branch. declarations in this block are not handled.
        if (stmt->if_stmt.then_stmt) {
            if (stmt->if_stmt.then_stmt->kind == SCOPE_NODE) {
                process_stmts_codegen(stmt->if_stmt.then_stmt->scope.statements, out, then_pred);
            } else {
                gen_statement(stmt->if_stmt.then_stmt, out, then_pred);
            }
        }

        // process the false branch.
        if (stmt->if_stmt.else_stmt) {
            // invert this condition for the false branch.
            int not_cond = gen_id();
            fprintf(out, "%%%-3d = OpLogicalNot %%t_bool %%%-3d\n", not_cond, cond_id);

            else_pred = not_cond;
            if (predicate_id > 0) {
                int combined = gen_id();
                fprintf(out, "%%%-3d = OpLogicalAnd %%t_bool %%%-3d %%%-3d\n", combined,
                        predicate_id, not_cond);
                else_pred = combined;
            }

            if (stmt->if_stmt.else_stmt->kind == SCOPE_NODE) {
                process_stmts_codegen(stmt->if_stmt.else_stmt->scope.statements, out, else_pred);
            } else {
                gen_statement(stmt->if_stmt.else_stmt, out, else_pred);
            }
        }
        break;
    }

    case SCOPE_NODE: {
        // process the nested scope.
        process_decls_allocate(stmt->scope.declarations, out);
        process_decls_initialize(stmt->scope.declarations, out);
        process_stmts_codegen(stmt->scope.statements, out, predicate_id);
        break;
    }

    default:
        fprintf(stderr, "warning - unimplemented statement kind %d\n", stmt->kind);
        break;
    }
}

void generate_code(node *ast, FILE *output) {
    if (!ast || ast->kind != SCOPE_NODE)
        return;

    // save the function body while constants are collected.
    char *func_body = NULL;
    size_t body_size = 0;
    FILE *body_stream = open_memstream(&func_body, &body_size);

    if (!body_stream) {
        fprintf(stderr, "error - failed to create memory stream\n");
        return;
    }

    fprintf(body_stream, "%%entry = OpLabel\n");

    // reserve storage for the outer scope before executable instructions.
    process_decls_allocate(ast->scope.declarations, body_stream);

    // write the initial variable values.
    process_decls_initialize(ast->scope.declarations, body_stream);

    // write statement instructions and collect their constants.
    process_stmts_codegen(ast->scope.statements, body_stream, 0);

    fprintf(body_stream, "OpReturn\n");
    fprintf(body_stream, "OpFunctionEnd\n");
    fclose(body_stream);

    // write the module in the required order.
    fprintf(output, "; SPIR-V\n");
    fprintf(output, "; Version: 1.0\n");
    fprintf(output, "; Generator: Shady\n");
    fprintf(output, "; Bound: %d\n", next_id);
    fprintf(output, "; Schema: 0\n");

    emit_prologue(output);

    // write constants before the function.
    fprintf(output, "; ---- shader constants ----\n");
    emit_constants(output);
    fprintf(output, "\n");

    // write the saved function body.
    fprintf(output, "%%main = OpFunction %%t_void None %%t_fn\n");
    fprintf(output, "%s", func_body);

    free(func_body);
    clear_local_vars();
}
