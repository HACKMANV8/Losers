import json, sys
from pathlib import Path
project_root = Path('.').resolve()
backend_root = project_root / 'iris-website' / 'backend'
sys.path.insert(0, str(backend_root))
sys.path.insert(0, str(project_root / 'iris-website'))
from services.llvm_optimization_service import LLVMOptimizationService
service = LLVMOptimizationService()
with open('tools/training_data/new_flattened_hybrid_data.json') as f:
    data = json.load(f)
for idx in range(5):
    sample = data[idx]
    features = {k: sample[k] for k in sample if k.startswith('feature_')}
    success, passes, error = service.predict_passes_with_transformer(features, beam_size=5)
    print(idx, success, passes[:20])
