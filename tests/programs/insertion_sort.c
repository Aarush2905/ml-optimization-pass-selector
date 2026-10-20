#include <stdio.h>

#define N 4000

static int arr[N];

void insertion_sort(int *a, int n) {
    for (int i = 1; i < n; i++) {
        int key = a[i];
        int j = i - 1;
        while (j >= 0 && a[j] > key) {
            a[j + 1] = a[j];
            j--;
        }
        a[j + 1] = key;
    }
}

int main() {
    long long checksum = 0;
    unsigned int seed = 777;
    for (int r = 0; r < 3; r++) {
        for (int i = 0; i < N; i++) {
            seed = seed * 1103515245u + 12345u;
            arr[i] = (int)((seed >> 8) % 50000);
        }
        insertion_sort(arr, N);
        for (int i = 0; i < N; i += 37) {
            checksum = (checksum * 31 + arr[i]) % 1000000007LL;
        }
    }
    printf("Insertion Sort Checksum: %lld\n", checksum);
    return 0;
}
