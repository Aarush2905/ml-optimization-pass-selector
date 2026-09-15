#include <stdio.h>

long long collatz_steps(long long n) {
    long long steps = 0;
    while (n > 1) {
        if (n % 2 == 0) {
            n = n / 2;
        } else {
            n = 3 * n + 1;
        }
        steps++;
    }
    return steps;
}

int main() {
    long long total_steps = 0;
    for (int r = 0; r < 20; r++) {
        for (long long i = 1; i <= 20000; i++) {
            total_steps += collatz_steps(i);
        }
    }
    printf("Collatz Total Steps: %lld\n", total_steps);
    return 0;
}
