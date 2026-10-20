#include <stdio.h>

int to_roman(int n, char *out) {
    int len = 0;
    while (n > 0) {
        if (n >= 1000) { out[len++] = 'M'; n -= 1000; }
        else if (n >= 900) { out[len++] = 'C'; out[len++] = 'M'; n -= 900; }
        else if (n >= 500) { out[len++] = 'D'; n -= 500; }
        else if (n >= 400) { out[len++] = 'C'; out[len++] = 'D'; n -= 400; }
        else if (n >= 100) { out[len++] = 'C'; n -= 100; }
        else if (n >= 90) { out[len++] = 'X'; out[len++] = 'C'; n -= 90; }
        else if (n >= 50) { out[len++] = 'L'; n -= 50; }
        else if (n >= 40) { out[len++] = 'X'; out[len++] = 'L'; n -= 40; }
        else if (n >= 10) { out[len++] = 'X'; n -= 10; }
        else if (n >= 9) { out[len++] = 'I'; out[len++] = 'X'; n -= 9; }
        else if (n >= 5) { out[len++] = 'V'; n -= 5; }
        else if (n >= 4) { out[len++] = 'I'; out[len++] = 'V'; n -= 4; }
        else { out[len++] = 'I'; n -= 1; }
    }
    out[len] = 0;
    return len;
}

int value_of(char c) {
    switch (c) {
        case 'I': return 1;
        case 'V': return 5;
        case 'X': return 10;
        case 'L': return 50;
        case 'C': return 100;
        case 'D': return 500;
        case 'M': return 1000;
        default: return 0;
    }
}

int from_roman(const char *s, int len) {
    int total = 0;
    for (int i = 0; i < len; i++) {
        int v = value_of(s[i]);
        if (i + 1 < len && v < value_of(s[i + 1])) total -= v;
        else total += v;
    }
    return total;
}

int main() {
    char buf[32];
    long long checksum = 0;
    int mismatches = 0;
    for (int r = 0; r < 25; r++) {
        for (int n = 1; n < 4000; n++) {
            int len = to_roman(n, buf);
            int back = from_roman(buf, len);
            if (back != n) mismatches++;
            checksum = (checksum + (long long)len * n) % 1000000007LL;
        }
    }
    printf("Roman Checksum: %lld, Mismatches: %d\n", checksum, mismatches);
    return 0;
}
