#include <stdio.h>

#define N 512

static int a[N][N];
static int b[N][N];

int main() {
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++)
            a[i][j] = (i * N + j) % 1009;

    long long checksum = 0;
    for (int r = 0; r < 10; r++) {
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                b[j][i] = a[i][j] + r;
        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                a[i][j] = b[i][j];
        checksum = (checksum + a[3][N - 5] + a[N / 2][7]) % 1000000007LL;
    }
    printf("Transpose Checksum: %lld\n", checksum);
    return 0;
}
