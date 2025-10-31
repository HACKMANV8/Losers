# Training Programs for ML-Guided Compiler Optimization

This directory contains **30 diverse C programs** used to train the ML model to predict optimal LLVM pass sequences. These programs are **separate from the test set** to ensure proper evaluation of model generalization.

## 📋 Training Suite Overview

### Sorting Algorithms (4 programs)
1. **01_insertion_sort.c** - O(n²) insertion sort (30K elements)
2. **02_selection_sort.c** - O(n²) selection sort (20K elements)
3. **03_counting_sort.c** - Linear time counting sort (100K elements)
4. **04_radix_sort.c** - Multi-digit radix sort (100K elements)

### Graph Algorithms (8 programs)
5. **05_bfs_graph.c** - Breadth-first search (8K vertices)
6. **06_floyd_warshall.c** - All-pairs shortest path (400 vertices)
7. **21_kruskal_mst.c** - Kruskal's MST with union-find (5K vertices, 20K edges)
8. **22_prim_mst.c** - Prim's MST algorithm (2K vertices)
9. **23_bellman_ford.c** - Single-source shortest path (3K vertices, 15K edges)
10. **24_topological_sort.c** - DAG topological ordering (10K vertices)
11. **25_strongly_connected.c** - Kosaraju's SCC algorithm (5K vertices)
12. **26_travelling_salesman.c** - TSP with backtracking (15 cities)

### Dynamic Programming (4 programs)
13. **07_matrix_chain.c** - Matrix chain multiplication DP (100 matrices)
14. **10_coin_change.c** - Coin change counting problem (n=5000)
15. **11_rod_cutting.c** - Rod cutting optimization (n=10000)
16. **12_subset_sum.c** - Subset sum problem (n=500, sum=10000)

### Matrix & Linear Algebra (2 programs)
17. **08_strassen_matrix.c** - Matrix multiplication (256×256)
18. **09_lu_decomposition.c** - LU matrix decomposition (400×400)

### String Algorithms (4 programs)
19. **13_rabin_karp.c** - Rolling hash string matching (500K chars)
20. **14_boyer_moore.c** - Boyer-Moore pattern matching (500K chars)
21. **15_aho_corasick.c** - Multi-pattern string matching (100K chars)
22. **16_suffix_array.c** - Suffix array construction (10K chars)

### Advanced Data Structures (4 programs)
23. **17_avl_tree.c** - Self-balancing AVL tree (30K inserts)
24. **18_red_black_tree.c** - Red-black tree operations (30K inserts)
25. **19_trie.c** - Prefix tree for strings (50K words)
26. **20_heap.c** - Min-heap with insert/extract (100K ops)

### Computational Problems (4 programs)
27. **27_n_queens.c** - N-Queens backtracking (n=13)
28. **28_sudoku_solver.c** - Sudoku solver with backtracking (1000 iterations)
29. **29_fast_fourier.c** - FFT algorithm (n=8192)
30. **30_monte_carlo_pi.c** - Monte Carlo π estimation (50M samples)

## 🎯 Purpose: Training the ML Model

### Data Generation Workflow

For each training program:
1. **Compile to LLVM IR**: `clang -S -emit-llvm program.c -o program.ll`
2. **Extract Features**: ~50 features (loops, branches, memory ops, etc.)
3. **Generate Pass Sequences**: 200-500 different sequences per program
4. **Apply & Measure**: Run each sequence, measure execution time & binary size
5. **Create Training Data**: `(features, sequence) → performance`

### Expected Training Dataset Size

```
30 programs × 300 sequences/program = 9,000 training samples
```

This provides sufficient data for XGBoost to learn patterns between:
- **Program characteristics** (features from LLVM IR)
- **Pass sequences** (which optimizations to apply)
- **Performance outcomes** (execution time, binary size)

## 📊 Coverage & Diversity

| Category | Count | Optimization Focus |
|----------|-------|-------------------|
| Sorting | 4 | Loop unrolling, vectorization |
| Graphs | 8 | Indirect memory, recursion |
| Dynamic Programming | 4 | Memory patterns, loop fusion |
| Matrix/Linear Algebra | 2 | Cache optimization, SIMD |
| Strings | 4 | Pattern matching, prefetching |
| Data Structures | 4 | Pointer aliasing, inlining |
| Computational | 4 | Branch prediction, recursion |

## 🔄 Difference from Test Programs

**Training Programs** (this directory):
- Used to teach the ML model
- Model sees these during training
- Learns optimization patterns from these

**Test Programs** (`../test_programs/`):
- Used to evaluate the ML model
- Model has NEVER seen these before
- Measures how well model generalizes

## 🚀 Next Steps

1. ✅ **Training programs created** (30 programs)
2. 🔄 **Build pass sequence generator** (generate 200-500 sequences per program)
3. 🔄 **Build feature extractor** (extract ~50 LLVM IR features)
4. 🔄 **Generate training dataset** (run sequences, measure performance)
5. ⏳ **Train XGBoost model** (learn features → performance mapping)
6. ⏳ **Evaluate on test set** (compare ML vs -O0/-O1/-O2/-O3)

## 💡 Key Characteristics

- **Algorithmic Diversity**: Different computation patterns respond to different optimizations
- **Computational Intensity**: Each runs long enough for meaningful measurements
- **Real-World Relevance**: Actual algorithms used in production
- **Optimization Sensitivity**: Clear performance differences between pass sequences

## 📝 Usage Example

```bash
# Compile a training program
clang -O2 01_insertion_sort.c -o insertion_O2

# Run it
./insertion_O2
# Output: Insertion sort: 30000 elements in 0.xyz seconds

# Generate LLVM IR for feature extraction
clang -S -emit-llvm 01_insertion_sort.c -o 01_insertion_sort.ll

# Apply custom pass sequence
opt -passes="mem2reg,loop-unroll,simplifycfg" 01_insertion_sort.ll -o optimized.ll
llc -march=riscv64 optimized.ll -o optimized.s
clang optimized.s -o insertion_custom
./insertion_custom
```

---

**Status**: ✅ All 30 training programs created and ready for dataset generation!
