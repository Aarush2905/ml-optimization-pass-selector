#include <stdio.h>

int binary_search(int arr[], int n, int target) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

int main() {
    int arr[256];
    for (int i = 0; i < 256; i++) {
        arr[i] = i * 3 + 1;
    }

    int hits = 0;
    for (int r = 0; r < 20000; r++) {
        for (int query = 0; query < 100; query++) {
            if (binary_search(arr, 256, query * 7) != -1) {
                hits++;
            }
        }
    }
    printf("Binary Search Hits: %d\n", hits);
    return 0;
}
