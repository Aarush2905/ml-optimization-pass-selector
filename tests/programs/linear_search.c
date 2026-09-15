#include <stdio.h>

int linear_search(int arr[], int n, int target) {
    for (int i = 0; i < n; i++) {
        if (arr[i] == target) return i;
    }
    return -1;
}

int main() {
    int arr[128];
    for (int i = 0; i < 128; i++) {
        arr[i] = (i * 17) % 251;
    }

    int found_count = 0;
    for (int r = 0; r < 20000; r++) {
        for (int q = 0; q < 50; q++) {
            if (linear_search(arr, 128, q * 5) >= 0) {
                found_count++;
            }
        }
    }
    printf("Linear Search Found: %d\n", found_count);
    return 0;
}
