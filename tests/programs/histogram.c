#include <stdio.h>

#define N 200000
#define BINS 256

static unsigned char data[N];
static int hist[BINS];

int main() {
    unsigned int seed = 2024;
    for (int i = 0; i < N; i++) {
        seed = seed * 1103515245u + 12345u;
        data[i] = (unsigned char)(seed >> 16);
    }

    long long checksum = 0;
    for (int r = 0; r < 20; r++) {
        for (int b = 0; b < BINS; b++) hist[b] = 0;
        for (int i = 0; i < N; i++) hist[(data[i] + r) & (BINS - 1)]++;
        int max_bin = 0;
        for (int b = 1; b < BINS; b++)
            if (hist[b] > hist[max_bin]) max_bin = b;
        checksum = (checksum * 31 + max_bin + hist[max_bin]) % 1000000007LL;
    }
    printf("Histogram Checksum: %lld\n", checksum);
    return 0;
}
