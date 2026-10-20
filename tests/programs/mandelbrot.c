#include <stdio.h>

#define W 200
#define H 150
#define MAX_ITER 200

int main() {
    long long total_iters = 0;
    int inside = 0;
    for (int py = 0; py < H; py++) {
        double y0 = (py / (double)H) * 2.4 - 1.2;
        for (int px = 0; px < W; px++) {
            double x0 = (px / (double)W) * 3.5 - 2.5;
            double x = 0.0, y = 0.0;
            int iter = 0;
            while (x * x + y * y <= 4.0 && iter < MAX_ITER) {
                double xt = x * x - y * y + x0;
                y = 2.0 * x * y + y0;
                x = xt;
                iter++;
            }
            total_iters += iter;
            if (iter == MAX_ITER) inside++;
        }
    }
    printf("Mandelbrot Iterations: %lld, Inside: %d\n", total_iters, inside);
    return 0;
}
