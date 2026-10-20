#include <stdio.h>

static long long moves = 0;
static long long weighted = 0;

void hanoi(int n, int from, int to, int via) {
    if (n == 0) return;
    hanoi(n - 1, from, via, to);
    moves++;
    weighted = (weighted + (long long)n * (from * 3 + to)) % 1000000007LL;
    hanoi(n - 1, via, to, from);
}

int main() {
    for (int r = 0; r < 4; r++) {
        hanoi(20, 0, 2, 1);
    }
    printf("Hanoi Moves: %lld, Weighted: %lld\n", moves, weighted);
    return 0;
}
