#include <stdio.h>

#define TABLE_SIZE 127
#define EMPTY -1

int table_keys[TABLE_SIZE];
int table_vals[TABLE_SIZE];

void init_table() {
    for (int i = 0; i < TABLE_SIZE; i++) {
        table_keys[i] = EMPTY;
        table_vals[i] = 0;
    }
}

void insert_entry(int key, int val) {
    int idx = (key * 2654435761U) % TABLE_SIZE;
    while (table_keys[idx] != EMPTY && table_keys[idx] != key) {
        idx = (idx + 1) % TABLE_SIZE;
    }
    table_keys[idx] = key;
    table_vals[idx] = val;
}

int lookup_entry(int key) {
    int idx = (key * 2654435761U) % TABLE_SIZE;
    int start = idx;
    while (table_keys[idx] != EMPTY) {
        if (table_keys[idx] == key) return table_vals[idx];
        idx = (idx + 1) % TABLE_SIZE;
        if (idx == start) break;
    }
    return -1;
}

int main() {
    int checksum = 0;
    for (int epoch = 0; epoch < 5000; epoch++) {
        init_table();
        for (int i = 0; i < 60; i++) {
            insert_entry(i * 13 + epoch, i * 7);
        }
        for (int i = 0; i < 60; i++) {
            checksum = (checksum + lookup_entry(i * 13 + epoch)) % 1000003;
        }
    }
    printf("Hash Table Checksum: %d\n", checksum);
    return 0;
}
