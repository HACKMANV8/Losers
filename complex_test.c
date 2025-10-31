#include <stdio.h>

// A function with loops and branches to generate more features
int calculate_sum(int max) {
    int sum = 0;
    for (int i = 0; i < max; i++) {
        if (i % 2 == 0) {
            sum += i;
        } else {
            sum -= 1;
        }
    }
    return sum;
}

int main() {
    int result = calculate_sum(100);
    printf("Result: %d\n", result);
    return 0;
}
