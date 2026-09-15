#include <stdio.h>

long long fact(int n) {
    if (n <= 1) return 1;
    return (long long)n * fact(n - 1);
}

int main() {
    long long total = 0;
    for (int r = 0; r < 50000; r++) {
        for (int i = 1; i <= 15; i++) {
            total = (total + fact(i)) % 1000000007LL;
        }
    }
    printf("Factorial Total: %lld\n", total);
    return 0;
}
