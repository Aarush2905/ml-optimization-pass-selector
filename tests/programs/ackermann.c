#include <stdio.h>

int ackermann(int m, int n) {
    if (m == 0) return n + 1;
    if (n == 0) return ackermann(m - 1, 1);
    return ackermann(m - 1, ackermann(m, n - 1));
}

int main() {
    long long total = 0;
    for (int r = 0; r < 20; r++) {
        for (int n = 0; n <= 6; n++) {
            total += ackermann(2, n * 10);
            total += ackermann(3, n);
        }
    }
    printf("Ackermann Total: %lld\n", total);
    return 0;
}
