#include <stdio.h>

#define N 32

void matrix_mult(int A[N][N], int B[N][N], int C[N][N]) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            C[i][j] = 0;
            for (int k = 0; k < N; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

int main() {
    int A[N][N], B[N][N], C[N][N];
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = (i + j) % 17;
            B[i][j] = (i * j + 1) % 19;
        }
    }

    for (int r = 0; r < 20; r++) {
        matrix_mult(A, B, C);
        A[0][0] = C[N-1][N-1] % 13;
    }

    int sum = 0;
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            sum = (sum + C[i][j]) % 1000007;
        }
    }
    printf("Matrix Sum: %d\n", sum);
    return 0;
}
