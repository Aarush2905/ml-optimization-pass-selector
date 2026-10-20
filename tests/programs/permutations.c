#include <stdio.h>

#define N 9

static int perm[N];
static int used[N];
static long long checksum = 0;
static long long count = 0;

void permute(int depth) {
    if (depth == N) {
        long long v = 0;
        for (int i = 0; i < N; i++) v = v * 10 + perm[i];
        checksum = (checksum + v % 1000003) % 1000000007LL;
        count++;
        return;
    }
    for (int i = 0; i < N; i++) {
        if (!used[i]) {
            used[i] = 1;
            perm[depth] = i;
            permute(depth + 1);
            used[i] = 0;
        }
    }
}

int main() {
    for (int r = 0; r < 2; r++) {
        permute(0);
    }
    printf("Permutations: %lld, Checksum: %lld\n", count, checksum);
    return 0;
}
