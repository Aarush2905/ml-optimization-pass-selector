#include <stdio.h>

#define W 256
#define H 256

static int image[H][W];
static int output[H][W];

static const int kernel[3][3] = {
    { 1, 2, 1 },
    { 2, 4, 2 },
    { 1, 2, 1 }
};

int main() {
    for (int y = 0; y < H; y++)
        for (int x = 0; x < W; x++)
            image[y][x] = (x * 7 + y * 13) % 256;

    long long checksum = 0;
    for (int r = 0; r < 8; r++) {
        for (int y = 1; y < H - 1; y++) {
            for (int x = 1; x < W - 1; x++) {
                int acc = 0;
                for (int ky = -1; ky <= 1; ky++)
                    for (int kx = -1; kx <= 1; kx++)
                        acc += image[y + ky][x + kx] * kernel[ky + 1][kx + 1];
                output[y][x] = acc / 16;
            }
        }
        for (int y = 0; y < H; y++)
            for (int x = 0; x < W; x++)
                image[y][x] = output[y][x];
        checksum = (checksum + output[H / 2][W / 2] + output[10][20]) % 1000000007LL;
    }
    printf("Convolution Checksum: %lld\n", checksum);
    return 0;
}
