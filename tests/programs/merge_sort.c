#include <stdio.h>

#define N 20000

static int arr[N];
static int tmp[N];

void merge(int *a, int lo, int mid, int hi) {
    int i = lo, j = mid + 1, k = lo;
    while (i <= mid && j <= hi) {
        if (a[i] <= a[j]) tmp[k++] = a[i++];
        else tmp[k++] = a[j++];
    }
    while (i <= mid) tmp[k++] = a[i++];
    while (j <= hi) tmp[k++] = a[j++];
    for (int x = lo; x <= hi; x++) a[x] = tmp[x];
}

void merge_sort(int *a, int lo, int hi) {
    if (lo >= hi) return;
    int mid = lo + (hi - lo) / 2;
    merge_sort(a, lo, mid);
    merge_sort(a, mid + 1, hi);
    merge(a, lo, mid, hi);
}

int main() {
    long long checksum = 0;
    unsigned int seed = 54321;
    for (int r = 0; r < 10; r++) {
        for (int i = 0; i < N; i++) {
            seed = seed * 1664525u + 1013904223u;
            arr[i] = (int)((seed >> 8) % 100000);
        }
        merge_sort(arr, 0, N - 1);
        for (int i = 0; i < N; i += 89) {
            checksum = (checksum * 31 + arr[i]) % 1000000007LL;
        }
    }
    printf("Merge Sort Checksum: %lld\n", checksum);
    return 0;
}
