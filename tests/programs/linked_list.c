#include <stdio.h>

#define POOL 50000

struct Node {
    int value;
    struct Node *next;
};

static struct Node pool[POOL];

struct Node *build_list(int n) {
    struct Node *head = 0;
    for (int i = 0; i < n; i++) {
        /* Scatter nodes across the pool to defeat sequential access */
        int idx = (int)(((long long)i * 7919) % POOL);
        pool[idx].value = (i * 37) % 1000;
        pool[idx].next = head;
        head = &pool[idx];
    }
    return head;
}

long long sum_list(struct Node *head) {
    long long s = 0;
    while (head) {
        s += head->value;
        head = head->next;
    }
    return s;
}

struct Node *reverse_list(struct Node *head) {
    struct Node *prev = 0;
    while (head) {
        struct Node *nx = head->next;
        head->next = prev;
        prev = head;
        head = nx;
    }
    return prev;
}

int main() {
    struct Node *head = build_list(POOL);
    long long checksum = 0;
    for (int r = 0; r < 100; r++) {
        head = reverse_list(head);
        checksum = (checksum + sum_list(head) + head->value) % 1000000007LL;
    }
    printf("Linked List Checksum: %lld\n", checksum);
    return 0;
}
