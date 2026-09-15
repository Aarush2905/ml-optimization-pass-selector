#include <stdio.h>

#define LIMIT 5000

int main() {
    char is_prime[LIMIT + 1];
    for (int i = 0; i <= LIMIT; i++) is_prime[i] = 1;
    is_prime[0] = is_prime[1] = 0;

    for (int p = 2; p * p <= LIMIT; p++) {
        if (is_prime[p]) {
            for (int i = p * p; i <= LIMIT; i += p) {
                is_prime[i] = 0;
            }
        }
    }

    int prime_count = 0;
    int sum_primes = 0;
    for (int i = 2; i <= LIMIT; i++) {
        if (is_prime[i]) {
            prime_count++;
            sum_primes = (sum_primes + i) % 100003;
        }
    }
    printf("Primes: %d, Sum: %d\n", prime_count, sum_primes);
    return 0;
}
