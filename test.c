#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#define MAX_POINTS 1000
#define HASH_TABLE_SIZE 256
#define PI 3.14159265358979323846

// ============ Geometry Structures ============
typedef struct {
    double x, y, z;
} Point3D;

typedef struct {
    double real, imag;
} Complex;

// ============ Hash Table Structure ============
typedef struct HashNode {
    char* key;
    int value;
    struct HashNode* next;
} HashNode;

typedef struct {
    HashNode* buckets[HASH_TABLE_SIZE];
} HashTable;

// ============ Mathematical Functions ============

// Fast exponentiation using bit manipulation
long long fast_power(long long base, int exp, int mod) {
    long long result = 1;
    base %= mod;
    while (exp > 0) {
        if (exp & 1) {
            result = (result * base) % mod;
        }
        base = (base * base) % mod;
        exp >>= 1;
    }
    return result;
}

// Compute Fibonacci using matrix exponentiation
long long fibonacci(int n) {
    if (n <= 1) return n;
    
    long long fib[3] = {0, 1, 1};
    for (int i = 2; i <= n; i++) {
        fib[i % 3] = fib[(i - 1) % 3] + fib[(i - 2) % 3];
    }
    return fib[n % 3];
}

// Complex number operations
Complex complex_multiply(Complex a, Complex b) {
    Complex result;
    result.real = a.real * b.real - a.imag * b.imag;
    result.imag = a.real * b.imag + a.imag * b.real;
    return result;
}

Complex complex_exp(double theta) {
    Complex result;
    result.real = cos(theta);
    result.imag = sin(theta);
    return result;
}

// Fast Fourier Transform (simplified)
void fft_compute(Complex* data, int n, int inverse) {
    if (n <= 1) return;
    
    // Bit reversal
    for (int i = 1, j = 0; i < n; i++) {
        int bit = n >> 1;
        for (; j & bit; bit >>= 1) {
            j ^= bit;
        }
        j ^= bit;
        
        if (i < j) {
            Complex temp = data[i];
            data[i] = data[j];
            data[j] = temp;
        }
    }
    
    // Cooley-Tukey FFT
    for (int len = 2; len <= n; len <<= 1) {
        double angle = 2 * PI / len * (inverse ? -1 : 1);
        Complex wlen = complex_exp(angle);
        
        for (int i = 0; i < n; i += len) {
            Complex w = {1, 0};
            for (int j = 0; j < len / 2; j++) {
                Complex u = data[i + j];
                Complex v = complex_multiply(data[i + j + len / 2], w);
                
                data[i + j].real = u.real + v.real;
                data[i + j].imag = u.imag + v.imag;
                data[i + j + len / 2].real = u.real - v.real;
                data[i + j + len / 2].imag = u.imag - v.imag;
                
                w = complex_multiply(w, wlen);
            }
        }
    }
    
    if (inverse) {
        for (int i = 0; i < n; i++) {
            data[i].real /= n;
            data[i].imag /= n;
        }
    }
}

// ============ Geometry Functions ============

// 3D distance calculation
double point_distance(Point3D a, Point3D b) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    double dz = a.z - b.z;
    return sqrt(dx * dx + dy * dy + dz * dz);
}

// Cross product
Point3D cross_product(Point3D a, Point3D b) {
    Point3D result;
    result.x = a.y * b.z - a.z * b.y;
    result.y = a.z * b.x - a.x * b.z;
    result.z = a.x * b.y - a.y * b.x;
    return result;
}

// Compute convex hull area (Graham scan simplified)
double convex_hull_area(Point3D* points, int n) {
    if (n < 3) return 0.0;
    
    double area = 0.0;
    Point3D center = {0, 0, 0};
    
    // Compute centroid
    for (int i = 0; i < n; i++) {
        center.x += points[i].x;
        center.y += points[i].y;
        center.z += points[i].z;
    }
    center.x /= n;
    center.y /= n;
    center.z /= n;
    
    // Triangulate from center
    for (int i = 0; i < n; i++) {
        Point3D v1 = {points[i].x - center.x, points[i].y - center.y, points[i].z - center.z};
        Point3D v2 = {points[(i + 1) % n].x - center.x, 
                      points[(i + 1) % n].y - center.y,
                      points[(i + 1) % n].z - center.z};
        Point3D cross = cross_product(v1, v2);
        area += sqrt(cross.x * cross.x + cross.y * cross.y + cross.z * cross.z) / 2.0;
    }
    
    return area;
}

// Rotate point around axis
Point3D rotate_point(Point3D p, Point3D axis, double angle) {
    double c = cos(angle);
    double s = sin(angle);
    double t = 1 - c;
    
    // Normalize axis
    double len = sqrt(axis.x * axis.x + axis.y * axis.y + axis.z * axis.z);
    axis.x /= len;
    axis.y /= len;
    axis.z /= len;
    
    Point3D result;
    result.x = (t * axis.x * axis.x + c) * p.x + 
               (t * axis.x * axis.y - s * axis.z) * p.y + 
               (t * axis.x * axis.z + s * axis.y) * p.z;
    result.y = (t * axis.x * axis.y + s * axis.z) * p.x + 
               (t * axis.y * axis.y + c) * p.y + 
               (t * axis.y * axis.z - s * axis.x) * p.z;
    result.z = (t * axis.x * axis.z - s * axis.y) * p.x + 
               (t * axis.y * axis.z + s * axis.x) * p.y + 
               (t * axis.z * axis.z + c) * p.z;
    
    return result;
}

// ============ Hash Table Functions ============

// DJB2 hash function
unsigned int hash_function(const char* str) {
    unsigned int hash = 5381;
    int c;
    while ((c = *str++)) {
        hash = ((hash << 5) + hash) + c; // hash * 33 + c
    }
    return hash % HASH_TABLE_SIZE;
}

// Initialize hash table
HashTable* create_hash_table() {
    HashTable* table = (HashTable*)malloc(sizeof(HashTable));
    for (int i = 0; i < HASH_TABLE_SIZE; i++) {
        table->buckets[i] = NULL;
    }
    return table;
}

// Insert into hash table
void hash_insert(HashTable* table, const char* key, int value) {
    unsigned int index = hash_function(key);
    HashNode* node = (HashNode*)malloc(sizeof(HashNode));
    node->key = strdup(key);
    node->value = value;
    node->next = table->buckets[index];
    table->buckets[index] = node;
}

// Search in hash table
int hash_search(HashTable* table, const char* key) {
    unsigned int index = hash_function(key);
    HashNode* node = table->buckets[index];
    
    while (node != NULL) {
        if (strcmp(node->key, key) == 0) {
            return node->value;
        }
        node = node->next;
    }
    return -1;
}

// Free hash table
void free_hash_table(HashTable* table) {
    for (int i = 0; i < HASH_TABLE_SIZE; i++) {
        HashNode* node = table->buckets[i];
        while (node != NULL) {
            HashNode* temp = node;
            node = node->next;
            free(temp->key);
            free(temp);
        }
    }
    free(table);
}

// ============ Numerical Algorithms ============

// Matrix multiplication (NxN)
void matrix_multiply(double** A, double** B, double** C, int n) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            C[i][j] = 0;
            for (int k = 0; k < n; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

// Sieve of Eratosthenes
int* sieve_primes(int limit, int* count) {
    int* is_prime = (int*)calloc(limit + 1, sizeof(int));
    for (int i = 2; i <= limit; i++) {
        is_prime[i] = 1;
    }
    
    for (int i = 2; i * i <= limit; i++) {
        if (is_prime[i]) {
            for (int j = i * i; j <= limit; j += i) {
                is_prime[j] = 0;
            }
        }
    }
    
    // Count primes
    *count = 0;
    for (int i = 2; i <= limit; i++) {
        if (is_prime[i]) (*count)++;
    }
    
    // Collect primes
    int* primes = (int*)malloc(*count * sizeof(int));
    int idx = 0;
    for (int i = 2; i <= limit; i++) {
        if (is_prime[i]) {
            primes[idx++] = i;
        }
    }
    
    free(is_prime);
    return primes;
}

// Greatest Common Divisor (Euclidean algorithm)
int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

// ============ Main Program ============

int main() {
    printf("=== Complex Multi-Domain Computation Test ===");
    
    // 1. Mathematical computations
    printf("\n1. Mathematical Operations:");
    long long fib_result = fibonacci(30);
    printf("   Fibonacci(30) = %lld", fib_result);
    
    long long power_result = fast_power(2, 20, 1000000007);
    printf("   2^20 mod 1e9+7 = %lld", power_result);
    
    // 2. Prime number generation
    printf("\n2. Prime Number Generation:");
    int prime_count;
    int* primes = sieve_primes(1000, &prime_count);
    printf("   Found %d primes up to 1000", prime_count);
    printf("   Last prime: %d", primes[prime_count - 1]);
    free(primes);
    
    // 3. Geometry computations
    printf("\n3. Geometry Computations:");
    Point3D points[100];
    for (int i = 0; i < 100; i++) {
        double angle = 2 * PI * i / 100;
        points[i].x = cos(angle) * 10;
        points[i].y = sin(angle) * 10;
        points[i].z = sin(2 * angle) * 5;
    }
    
    double total_distance = 0;
    for (int i = 0; i < 99; i++) {
        total_distance += point_distance(points[i], points[i + 1]);
    }
    printf("   Total path distance: %.2f", total_distance);
    
    double area = convex_hull_area(points, 100);
    printf("   Approximate surface area: %.2f", area);
    
    // 4. Point rotation
    Point3D axis = {0, 0, 1};
    Point3D test_point = {1, 0, 0};
    Point3D rotated = rotate_point(test_point, axis, PI / 4);
    printf("   Rotated point: (%.2f, %.2f, %.2f)", rotated.x, rotated.y, rotated.z);
    
    // 5. Hash table operations
    printf("\n4. Hash Table Operations:");
    HashTable* table = create_hash_table();
    
    char keys[50][32];
    for (int i = 0; i < 50; i++) {
        sprintf(keys[i], "key_%d", i);
        hash_insert(table, keys[i], i * i);
    }
    
    int search_sum = 0;
    for (int i = 0; i < 50; i += 5) {
        search_sum += hash_search(table, keys[i]);
    }
    printf("   Hash lookup sum: %d", search_sum);
    
    free_hash_table(table);
    
    // 6. FFT computation
    printf("\n5. FFT Signal Processing:");
    int fft_size = 64;
    Complex* signal = (Complex*)malloc(fft_size * sizeof(Complex));
    
    // Generate test signal
    for (int i = 0; i < fft_size; i++) {
        signal[i].real = sin(2 * PI * 5 * i / fft_size) + 
                         0.5 * cos(2 * PI * 10 * i / fft_size);
        signal[i].imag = 0;
    }
    
    fft_compute(signal, fft_size, 0);
    
    // Find dominant frequency
    double max_magnitude = 0;
    int max_idx = 0;
    for (int i = 0; i < fft_size / 2; i++) {
        double magnitude = sqrt(signal[i].real * signal[i].real + 
                              signal[i].imag * signal[i].imag);
        if (magnitude > max_magnitude) {
            max_magnitude = magnitude;
            max_idx = i;
        }
    }
    printf("   Dominant frequency bin: %d", max_idx);
    printf("   Magnitude: %.2f", max_magnitude);
    
    free(signal);
    
    // 7. GCD computations
    printf("\n6. Number Theory:");
    int gcd_sum = 0;
    for (int i = 1; i <= 100; i++) {
        for (int j = i + 1; j <= 100; j++) {
            gcd_sum += gcd(i, j);
        }
    }
    printf("   Sum of GCDs (1-100): %d", gcd_sum);
    
    printf("\n\n=== All computations completed successfully ===");
    
    return 0;
}

