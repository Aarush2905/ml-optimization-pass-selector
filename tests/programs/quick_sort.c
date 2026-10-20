#include <stdio.h>

#define N 20000

static int arr[N];

void swap(int *a, int *b) {
    int t = *a;
    *a = *b;
    *b = t;
}

int partition(int *a, int lo, int hi) {
    int pivot = a[hi];
    int i = lo - 1;
    for (int j = lo; j < hi; j++) {
        if (a[j] <= pivot) {
            i++;
            swap(&a[i], &a[j]);
        }
    }
    swap(&a[i + 1], &a[hi]);
    return i + 1;
}

void quick_sort(int *a, int lo, int hi) {
    if (lo < hi) {
        int p = partition(a, lo, hi);
        quick_sort(a, lo, p - 1);
        quick_sort(a, p + 1, hi);
    }
}

int main() {
    long long checksum = 0;
    unsigned int seed = 12345;
    for (int r = 0; r < 10; r++) {
        for (int i = 0; i < N; i++) {
            seed = seed * 1103515245u + 12345u;
            arr[i] = (int)((seed >> 8) % 100000);
        }
        quick_sort(arr, 0, N - 1);
        for (int i = 0; i < N; i += 97) {
            checksum = (checksum * 31 + arr[i]) % 1000000007LL;
        }
    }
    printf("Quick Sort Checksum: %lld\n", checksum);
    return 0;
}
