# Remaining Programs for Training (160 more needed)

Current: 40 programs (30 original + 10 new)
Target: 200 programs
**Need: 160 more diverse programs**

## Categories for Maximum Feature Diversity

### 1. Dense Linear Algebra (20 programs)
- [x] 31_dense_gemm.c (done)
- [x] 32_blocked_gemm.c (done)
- [ ] 41_gemv_variants.c - Matrix-vector multiply (row-major, column-major)
- [ ] 42_cholesky_decomposition.c - Symmetric positive definite solver
- [ ] 43_qr_decomposition.c - QR factorization using Householder
- [ ] 44_svd_2x2.c - Singular value decomposition for small matrices
- [ ] 45_tridiagonal_solver.c - Thomas algorithm for tridiagonal systems
- [ ] 46_jacobi_eigenvalue.c - Jacobi method for eigenvalues
- [ ] 47_power_iteration.c - Dominant eigenvalue finder
- [ ] 48_gram_schmidt.c - Orthogonalization process
- [ ] 49_matrix_inverse_3x3.c - Direct inversion formulas
- [ ] 50_kronecker_product.c - Tensor product of matrices
- [ ] 51_hadamard_product.c - Element-wise operations
- [ ] 52_matrix_exponential.c - Using series expansion
- [ ] 53_sparse_gemv.c - Compressed sparse row format
- [ ] 54_banded_matrix_solve.c - Exploiting band structure
- [ ] 55_toeplitz_solver.c - Levinson recursion
- [ ] 56_circulant_matrix.c - FFT-based operations
- [ ] 57_rank_one_update.c - Sherman-Morrison formula
- [ ] 58_blocked_lu.c - Cache-optimized LU with pivoting

### 2. Signal Processing & FFT (15 programs)
- [ ] 59_fft_radix2.c - Cooley-Tukey FFT
- [ ] 60_fft_radix4.c - Radix-4 variant
- [ ] 61_fft_real.c - Real-valued FFT optimization
- [ ] 62_dct_type2.c - Discrete cosine transform
- [ ] 63_convolution_1d.c - Direct convolution
- [ ] 64_fir_filter.c - Finite impulse response filter
- [ ] 65_iir_filter.c - Infinite impulse response (recursive)
- [ ] 66_window_functions.c - Hamming, Hann, Blackman
- [ ] 67_autocorrelation.c - Signal correlation
- [ ] 68_cross_correlation.c - Two-signal correlation
- [ ] 69_spectrogram.c - Short-time Fourier transform
- [ ] 70_cepstrum.c - Inverse FFT of log magnitude
- [ ] 71_hilbert_transform.c - Analytic signal generation
- [ ] 72_goertzel_algorithm.c - DFT of single frequency
- [ ] 73_chirp_z_transform.c - Generalized DFT

### 3. Image Processing (15 programs)
- [x] 34_gaussian_blur.c (done)
- [ ] 74_sobel_edge.c - Edge detection filter
- [ ] 75_median_filter.c - Noise reduction (sorting-based)
- [ ] 76_bilateral_filter.c - Edge-preserving smoothing
- [ ] 77_histogram_equalization.c - Contrast enhancement
- [ ] 78_morphology_dilate.c - Binary image dilation
- [ ] 79_morphology_erode.c - Binary image erosion
- [ ] 80_connected_components.c - Label connected regions
- [ ] 81_hough_transform.c - Line detection
- [ ] 82_harris_corner.c - Corner detection
- [ ] 83_canny_edge.c - Multi-stage edge detector
- [ ] 84_integral_image.c - Summed area table
- [ ] 85_template_matching.c - Pattern search in image
- [ ] 86_seam_carving.c - Content-aware image resizing
- [ ] 87_watershed.c - Image segmentation

### 4. String & Parsing (15 programs)
- [ ] 88_kmp_search.c - Knuth-Morris-Pratt pattern matching
- [ ] 89_z_algorithm.c - Linear-time pattern matching
- [ ] 90_manacher_palindrome.c - Longest palindrome in linear time
- [ ] 91_edit_distance_variants.c - Levenshtein with different costs
- [ ] 92_longest_common_substring.c - DP-based LCS
- [ ] 93_regex_nfa.c - NFA-based regex matcher
- [ ] 94_json_parser_lite.c - Simple JSON validator/parser
- [ ] 95_xml_sax_parser.c - Streaming XML parser
- [ ] 96_csv_parser.c - RFC 4180 compliant CSV
- [ ] 97_url_parser.c - URI component extraction
- [ ] 98_base64_encode.c - Binary to text encoding
- [ ] 99_base64_decode.c - Text to binary decoding
- [ ] 100_utf8_validator.c - UTF-8 sequence validation
- [ ] 101_rope_string.c - Rope data structure operations
- [ ] 102_burrows_wheeler.c - BWT transform for compression

### 5. Compression & Encoding (12 programs)
- [x] 35_lz77_compression.c (done)
- [ ] 103_lz77_decompress.c - Decompression counterpart
- [ ] 104_lzss_compression.c - LZSS variant
- [ ] 105_rle_encode.c - Run-length encoding
- [ ] 106_rle_decode.c - Run-length decoding
- [ ] 107_huffman_encode.c - Huffman tree construction + encoding
- [ ] 108_huffman_decode.c - Huffman decoding
- [ ] 109_arithmetic_coding.c - Range-based compression
- [ ] 110_deflate_lite.c - LZ77 + Huffman combination
- [ ] 111_bwt_encoding.c - Burrows-Wheeler transform
- [ ] 112_mtf_encoding.c - Move-to-front transform
- [ ] 113_delta_encoding.c - Differential encoding

### 6. Cryptography & Hashing (15 programs)
- [x] 38_aes_sbox.c (done)
- [ ] 114_md5_lite.c - MD5 hash (educational)
- [ ] 115_sha256_lite.c - SHA-256 hash
- [ ] 116_crc32.c - CRC-32 checksum
- [ ] 117_adler32.c - Adler-32 checksum
- [ ] 118_murmur_hash.c - Non-cryptographic hash
- [ ] 119_fnv_hash.c - Fowler-Noll-Vo hash
- [ ] 120_rc4_cipher.c - Stream cipher
- [ ] 121_xor_cipher.c - Simple XOR encryption
- [ ] 122_caesar_cipher.c - Substitution cipher
- [ ] 123_vigenere_cipher.c - Polyalphabetic cipher
- [ ] 124_des_sbox.c - DES S-box operations
- [ ] 125_rsa_modexp.c - Modular exponentiation for RSA
- [ ] 126_diffie_hellman.c - Key exchange simulation
- [ ] 127_bloom_filter.c - Probabilistic membership test

### 7. Numerical Methods (12 programs)
- [x] 37_simpson_integration.c (done)
- [ ] 128_romberg_integration.c - Richardson extrapolation
- [ ] 129_gauss_quadrature.c - Gaussian integration
- [ ] 130_newton_raphson.c - Root finding
- [ ] 131_secant_method.c - Root finding without derivatives
- [ ] 132_bisection_method.c - Bracketing root finder
- [ ] 133_runge_kutta_4.c - ODE solver (4th order)
- [ ] 134_euler_method.c - Simple ODE solver
- [ ] 135_adams_bashforth.c - Multistep ODE solver
- [ ] 136_gauss_seidel.c - Iterative linear system solver
- [ ] 137_conjugate_gradient.c - Iterative solver for SPD
- [ ] 138_newton_optimization.c - Multivariate optimization

### 8. Physics & Simulation (12 programs)
- [x] 36_nbody_simulation.c (done)
- [ ] 139_heat_diffusion_2d.c - Finite difference heat equation
- [ ] 140_wave_equation_1d.c - Wave propagation
- [ ] 141_laplace_equation.c - Potential field solver
- [ ] 142_molecular_dynamics.c - Lennard-Jones potential
- [ ] 143_spring_mass_system.c - Damped oscillator network
- [ ] 144_rigid_body_rotation.c - Quaternion-based rotation
- [ ] 145_fluid_lattice_boltzmann.c - LBM method (simple)
- [ ] 146_raytracing_spheres.c - Ray-sphere intersection
- [ ] 147_collision_detection.c - AABB and sphere collision
- [ ] 148_particle_swarm.c - PSO optimization
- [ ] 149_barnes_hut_nbody.c - Tree-based N-body

### 9. Graph Algorithms (Advanced) (12 programs)
- [ ] 150_max_flow_ford_fulkerson.c - Network flow
- [ ] 151_min_cost_flow.c - Cost-constrained flow
- [ ] 152_bipartite_matching.c - Hungarian algorithm
- [ ] 153_stable_marriage.c - Gale-Shapley algorithm
- [ ] 154_articulation_points.c - Graph cut vertices
- [ ] 155_bridges_tarjan.c - Graph bridges
- [ ] 156_eulerian_path.c - Hierholzer's algorithm
- [ ] 157_hamiltonian_cycle.c - Backtracking search
- [ ] 158_chromatic_coloring.c - Graph coloring heuristic
- [ ] 159_vertex_cover.c - Approximation algorithm
- [ ] 160_steiner_tree.c - Minimum spanning tree variant
- [ ] 161_all_pairs_shortest_path.c - Johnson's algorithm

### 10. Computational Geometry (10 programs)
- [x] 39_convex_hull.c (done)
- [ ] 162_line_intersection.c - Bentley-Ottmann algorithm
- [ ] 163_closest_pair.c - Divide and conquer
- [ ] 164_voronoi_diagram.c - Fortune's algorithm (simplified)
- [ ] 165_delaunay_triangulation.c - Incremental insertion
- [ ] 166_polygon_triangulation.c - Ear clipping method
- [ ] 167_point_in_polygon.c - Ray casting algorithm
- [ ] 168_polygon_area.c - Shoelace formula
- [ ] 169_minkowski_sum.c - Configuration space
- [ ] 170_rotating_calipers.c - Diameter of convex polygon

### 11. Bit Manipulation & Optimization (10 programs)
- [x] 33_bitboard_chess.c (done)
- [ ] 171_popcount_variants.c - Various bit counting methods
- [ ] 172_bit_reversal.c - Reverse bits in word
- [ ] 173_gray_code.c - Binary to Gray code conversion
- [ ] 174_next_permutation_bits.c - Gosper's hack
- [ ] 175_bitset_operations.c - Set operations on bitmasks
- [ ] 176_parity_check.c - Even/odd parity
- [ ] 177_leading_zeros.c - CLZ implementations
- [ ] 178_bit_interleaving.c - Morton code (Z-order)
- [ ] 179_bitwise_gcd.c - Binary GCD algorithm

### 12. Game & Puzzle Solvers (10 programs)
- [ ] 180_tic_tac_toe_minimax.c - Game tree search
- [ ] 181_connect_four.c - Alpha-beta pruning
- [ ] 182_rubiks_cube_2x2.c - Pocket cube solver
- [ ] 183_fifteen_puzzle.c - IDA* search
- [ ] 184_maze_generation.c - Recursive backtracker
- [ ] 185_maze_solver.c - A* pathfinding
- [ ] 186_sokoban_solver.c - Pushing box puzzle
- [ ] 187_nonogram_solver.c - Picture logic puzzle
- [ ] 188_kakuro_solver.c - Cross-sum puzzle
- [ ] 189_kenken_solver.c - Arithmetic puzzle

### 13. Fractals & Chaos (8 programs)
- [x] 40_mandelbrot.c (done)
- [ ] 190_julia_set.c - Julia fractal generator
- [ ] 191_burning_ship.c - Burning ship fractal
- [ ] 192_lorenz_attractor.c - Chaotic system simulation
- [ ] 193_logistic_map.c - Bifurcation diagram
- [ ] 194_sierpinski_triangle.c - Fractal generation
- [ ] 195_koch_snowflake.c - Recursive fractal
- [ ] 196_dragon_curve.c - Paper-folding fractal

### 14. Miscellaneous Algorithms (4 programs)
- [ ] 197_expression_evaluator.c - Shunting yard + eval
- [ ] 198_polynomial_multiplication.c - FFT-based
- [ ] 199_sieve_of_eratosthenes.c - Prime number generation
- [ ] 200_chinese_remainder_theorem.c - Modular arithmetic

## Feature Diversity Goals

Ensure distribution across:
- **Loop nesting**: 30% single-loop, 40% double-loop, 30% triple+ loop
- **Branch intensity**: 30% low (<0.1), 40% medium (0.1-0.3), 30% high (>0.3)
- **Memory intensity**: 30% low (<0.3), 40% medium (0.3-0.6), 30% high (>0.6)
- **Arithmetic intensity**: 30% low (<0.1), 40% medium (0.1-0.3), 30% high (>0.3)
- **Call intensity**: 50% low (0-0.05), 30% medium (0.05-0.15), 20% high (>0.15)
- **Data types**: 40% int-heavy, 30% float-heavy, 30% mixed
- **Cyclomatic complexity**: 30% simple (<5), 40% moderate (5-15), 30% complex (>15)

## Implementation Priority

1. **Phase 1** (High priority): Complete categories 1-6 (87 programs) - diverse computational patterns
2. **Phase 2** (Medium priority): Categories 7-10 (46 programs) - specialized algorithms
3. **Phase 3** (Low priority): Categories 11-14 (27 programs) - niche but diverse

## Notes
- Each program should run in 10-1000ms for deterministic workload
- Include timing and simple output validation
- Use fixed seeds for reproducibility
- Avoid external dependencies (only standard C library)
- Target 300-1500 LOC per program for "big" programs
