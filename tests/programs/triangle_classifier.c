#include <stdio.h>

/* 0 invalid, 1 equilateral, 2 isosceles-right, 3 isosceles-acute, 4 isosceles-obtuse,
   5 scalene-right, 6 scalene-acute, 7 scalene-obtuse */
int classify(int a, int b, int c) {
    if (a <= 0 || b <= 0 || c <= 0) {
        return 0;
    } else {
        if (a + b <= c || a + c <= b || b + c <= a) {
            return 0;
        } else {
            int hi = a, x = b, y = c;
            if (b > hi) { hi = b; x = a; y = c; }
            if (c > hi) { hi = c; x = a; y = b; }
            long long lhs = (long long)x * x + (long long)y * y;
            long long rhs = (long long)hi * hi;
            if (a == b && b == c) {
                return 1;
            } else if (a == b || b == c || a == c) {
                if (lhs == rhs) {
                    return 2;
                } else if (lhs > rhs) {
                    return 3;
                } else {
                    return 4;
                }
            } else {
                if (lhs == rhs) {
                    return 5;
                } else if (lhs > rhs) {
                    return 6;
                } else {
                    return 7;
                }
            }
        }
    }
}

int main() {
    int counts[8] = {0};
    for (int r = 0; r < 4; r++) {
        for (int a = 1; a <= 60; a++) {
            for (int b = 1; b <= 60; b++) {
                for (int c = 1; c <= 60; c++) {
                    counts[classify(a, b, c)]++;
                }
            }
        }
    }
    printf("Triangles:");
    for (int i = 0; i < 8; i++) printf(" %d", counts[i]);
    printf("\n");
    return 0;
}
