#ifndef SHADY_SYMBOL_H
#define SHADY_SYMBOL_H

// store one entry for each variable.
typedef struct symbol_entry {
    char *name;    // store the variable name.
    int type_code; // the type from the parser.
    int vec_size;  // zero means scalar. vector sizes are the component count minus one.
    int is_const;
    int is_write_only; // set for output variables.
    int is_read_only;  // set for input variables.
} symbol_entry;

// store the names declared in one scope.
typedef struct symbol_table {
    symbol_entry **entries;      // point to the table entries.
    int size;                    // store the number of table slots.
    int count;                   // store the number of occupied slots.
    struct symbol_table *parent; // point to the enclosing scope.
} symbol_table;

symbol_table *symbol_table_create(symbol_table *parent);
void symbol_table_free(symbol_table *table);
int symbol_table_insert(symbol_table *table, symbol_entry *entry);
symbol_entry *symbol_table_lookup(symbol_table *table, const char *name);
symbol_entry *symbol_table_lookup_local(symbol_table *table,
                                        const char *name); // search only this scope.

#endif
