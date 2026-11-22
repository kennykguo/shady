#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include "symbol.h"

#define INITIAL_CAPACITY 128

// convert a name into a hash value.
static unsigned int hash(const char *str) {
    unsigned int hash = 0;
    while (*str) {
        hash = (hash * 31) + *str;
        str++;
    }
    return hash;
}

static void *allocate(size_t count, size_t size) {
    void *memory = calloc(count, size);
    if (!memory) {
        fputs("out of memory while allocating symbol table\n", stderr);
        exit(EXIT_FAILURE);
    }
    return memory;
}

/* keep empty slots so a search for an unknown name can stop. */
static void grow(symbol_table *table) {
    int old_size = table->size;
    symbol_entry **old_entries = table->entries;
    table->size *= 2;
    table->entries = allocate(table->size, sizeof(*table->entries));
    for (int i = 0; i < old_size; i++) {
        if (!old_entries[i])
            continue;
        unsigned int index = hash(old_entries[i]->name) % table->size;
        while (table->entries[index])
            index = (index + 1) % table->size;
        table->entries[index] = old_entries[i];
    }
    free(old_entries);
}

symbol_table *symbol_table_create(symbol_table *parent) {
    symbol_table *table = allocate(1, sizeof(*table));
    table->entries = allocate(INITIAL_CAPACITY, sizeof(*table->entries));
    table->size = INITIAL_CAPACITY;
    table->count = 0;
    table->parent = parent;
    return table;
}

void symbol_table_free(symbol_table *table) {
    if (!table)
        return;
    for (int i = 0; i < table->size; i++) {
        if (table->entries[i]) {
            free(table->entries[i]->name);
            free(table->entries[i]);
        }
    }
    free(table->entries);
    free(table);
}

int symbol_table_insert(symbol_table *table, symbol_entry *entry) {
    // check for a duplicate name in this scope.
    if (symbol_table_lookup_local(table, entry->name)) {
        return 0; // report a duplicate declaration.
    }
    // check each following slot until an empty slot is found.
    if ((table->count + 1) * 4 >= table->size * 3)
        grow(table);
    unsigned int index = hash(entry->name) % table->size;
    while (table->entries[index] != NULL) {
        index = (index + 1) % table->size;
    }
    table->entries[index] = entry;
    table->count++;
    return 1; // report success.
}

symbol_entry *symbol_table_lookup_local(symbol_table *table, const char *name) {
    if (!table)
        return NULL;
    unsigned int index = hash(name) % table->size;
    int probes = 0;
    while (table->entries[index] != NULL && probes < table->size) {
        if (strcmp(table->entries[index]->name, name) == 0) {
            return table->entries[index];
        }
        index = (index + 1) % table->size;
        probes++;
    }
    return NULL;
}

symbol_entry *symbol_table_lookup(symbol_table *table, const char *name) {
    if (!table)
        return NULL;
    // search this scope first.
    symbol_entry *entry = symbol_table_lookup_local(table, name);
    if (entry)
        return entry;
    // search the parent scope if the name was not found.
    if (table->parent) {
        return symbol_table_lookup(table->parent, name);
    }
    return NULL;
}
