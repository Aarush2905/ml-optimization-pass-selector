#include <stdio.h>

int process_value(int val, int mode) {
    switch (mode % 8) {
        case 0:
            if (val > 100) return val * 2;
            else if (val > 50) return val + 25;
            return val - 5;
        case 1:
            if (val % 2 == 0) return val / 2;
            return val * 3 + 1;
        case 2:
            return (val ^ 0xAA55) & 0xFFFF;
        case 3:
            if (val < 0) return -val;
            return val + 10;
        case 4:
            return (val * 7) % 997;
        case 5:
            if (val % 3 == 0) return val + 33;
            else if (val % 3 == 1) return val + 66;
            return val + 99;
        case 6:
            return val >> 2;
        default:
            return val + 1;
    }
}

int main() {
    int total = 0;
    for (int r = 0; r < 200000; r++) {
        total = (total + process_value(r % 500, r)) % 1000007;
    }
    printf("Branch Heavy Total: %d\n", total);
    return 0;
}
