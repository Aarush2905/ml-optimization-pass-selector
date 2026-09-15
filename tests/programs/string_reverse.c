#include <stdio.h>
#include <string.h>

void reverse_str(char *str, int len) {
    int i = 0, j = len - 1;
    while (i < j) {
        char tmp = str[i];
        str[i] = str[j];
        str[j] = tmp;
        i++;
        j--;
    }
}

int main() {
    char buf[128];
    const char *base = "OptimizationPassSelectorLLVMCompilerDesignLabReview2Prototype";
    int len = 0;
    while (base[len]) {
        buf[len] = base[len];
        len++;
    }
    buf[len] = '\0';

    int checksum = 0;
    for (int r = 0; r < 200000; r++) {
        reverse_str(buf, len);
        checksum += buf[r % len];
    }
    printf("String Checksum: %d\n", checksum);
    return 0;
}
