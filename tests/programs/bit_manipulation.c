#include <stdio.h>

unsigned int count_set_bits(unsigned int n) {
    unsigned int count = 0;
    while (n) {
        count += n & 1;
        n >>= 1;
    }
    return count;
}

unsigned int reverse_bits(unsigned int n) {
    unsigned int rev = 0;
    for (int i = 0; i < 32; i++) {
        if ((n & (1 << i))) {
            rev |= 1 << (31 - i);
        }
    }
    return rev;
}

int main() {
    unsigned int total = 0;
    for (unsigned int i = 1; i <= 50000; i++) {
        unsigned int bits = count_set_bits(i);
        unsigned int rev = reverse_bits(i ^ (i << 3));
        total += (bits * 31) ^ rev;
    }
    printf("Bit Total: %u\n", total);
    return 0;
}
