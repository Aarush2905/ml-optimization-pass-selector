#include <stdio.h>

int fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);
}

int main() {
    int total = 0;
    for (int i = 1; i <= 28; i++) {
        total += fib(i);
    }
    printf("Fibonacci Sum: %d\n", total);
    return 0;
}
