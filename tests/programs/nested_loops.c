#include <stdio.h>

int main() {
    long long accumulator = 0;
    int limit1 = 40;
    int limit2 = 50;
    int limit3 = 60;

    for (int iter = 0; iter < 100; iter++) {
        for (int i = 0; i < limit1; i++) {
            for (int j = 0; j < limit2; j++) {
                for (int k = 0; k < limit3; k++) {
                    accumulator = (accumulator + (i * j) - k + iter) % 1000000009LL;
                }
            }
        }
    }
    printf("Nested Loop Accumulator: %lld\n", accumulator);
    return 0;
}
