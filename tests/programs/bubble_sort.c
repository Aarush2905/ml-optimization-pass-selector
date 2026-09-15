#include <stdio.h>

void bubble_sort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int main() {
    int arr[64];
    for (int i = 0; i < 64; i++) {
        arr[i] = (64 - i) * 3 % 97;
    }
    for (int r = 0; r < 200; r++) {
        bubble_sort(arr, 64);
    }
    int checksum = 0;
    for (int i = 0; i < 64; i++) {
        checksum += arr[i] * (i + 1);
    }
    printf("Checksum: %d\n", checksum);
    return 0;
}
