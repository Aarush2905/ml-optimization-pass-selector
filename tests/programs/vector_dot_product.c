#include <stdio.h>

#define SIZE 256

int dot_product(const int *a, const int *b, int n) {
    int sum = 0;
    for (int i = 0; i < n; i++) {
        sum += a[i] * b[i];
    }
    return sum;
}

int main() {
    int a[SIZE], b[SIZE];
    for (int i = 0; i < SIZE; i++) {
        a[i] = (i * 7 + 3) % 101;
        b[i] = (i * 13 + 5) % 103;
    }

    int total = 0;
    for (int r = 0; r < 200000; r++) {
        total = (total + dot_product(a, b, SIZE)) % 100000007;
        a[r % SIZE] ^= 1;
    }
    printf("Dot Product Result: %d\n", total);
    return 0;
}
