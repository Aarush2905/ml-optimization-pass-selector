#include <stdio.h>

#define MAXN 12

static int cols[MAXN];

int is_safe(int row, int col) {
    for (int r = 0; r < row; r++) {
        int c = cols[r];
        if (c == col) return 0;
        if (c - col == r - row) return 0;
        if (c - col == row - r) return 0;
    }
    return 1;
}

int solve(int row, int n) {
    if (row == n) return 1;
    int count = 0;
    for (int col = 0; col < n; col++) {
        if (is_safe(row, col)) {
            cols[row] = col;
            count += solve(row + 1, n);
        }
    }
    return count;
}

int main() {
    long long total = 0;
    for (int n = 4; n <= 10; n++) {
        int s = solve(0, n);
        total = total * 7 + s;
    }
    printf("N-Queens Total: %lld\n", total);
    return 0;
}
