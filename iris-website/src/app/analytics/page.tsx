'use client';

import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import API_ENDPOINTS from '@/config/api';

interface ModelInfo {
  available: boolean;
  path?: string;
  device?: string;
  vocab_size?: number;
  num_features?: number;
}

interface ModelsData {
  models: {
    transformer?: ModelInfo;
    xgboost?: ModelInfo;
  };
  available: string[];
  total_available: number;
}

interface FeaturesData {
  total_features: number;
  feature_names: string[];
  feature_categories: Record<string, string>;
  extraction_method: string;
  target_architecture: string;
}

interface PassesData {
  total_passes: number;
  common_passes: Record<string, string>;
  optimization_levels: Record<string, string>;
}

interface SystemData {
  tools_available: Record<string, boolean>;
  all_tools_ready: boolean;
  versions?: Record<string, string>;
  target_architecture: string;
}

const Spinner = () => (
  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
);

export default function Analytics() {
  const [modelsData, setModelsData] = useState<ModelsData | null>(null);
  const [featuresData, setFeaturesData] = useState<FeaturesData | null>(null);
  const [passesData, setPassesData] = useState<PassesData | null>(null);
  const [systemData, setSystemData] = useState<SystemData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setLoading(true);
      setError(null);

      try {
        // Check if backend is available
        const healthRes = await fetch(API_ENDPOINTS.health);
        
        if (healthRes.ok) {
          // Backend is available, show static analytics info
          // Set static data about the system
          setModelsData({
            models: {
              xgboost: {
                available: true,
                path: 'models/xgboost_model.json',
                num_features: 73
              }
            },
            available: ['xgboost'],
            total_available: 1
          });
          
          setFeaturesData({
            total_features: 73,
            feature_names: ['total_instructions', 'total_basic_blocks', 'num_functions', 'cyclomatic_complexity', 'and more...'],
            feature_categories: {
              'Instruction Counts': '40+ features',
              'Control Flow': '15+ features',
              'Memory Operations': '10+ features',
              'Function Analysis': '8+ features'
            },
            extraction_method: 'LLVM IR Analysis',
            target_architecture: 'RISC-V 64-bit'
          });
          
          setPassesData({
            total_passes: 50,
            common_passes: {
              'mem2reg': 'Promote memory to register',
              'simplifycfg': 'Simplify control flow graph',
              'instcombine': 'Combine redundant instructions',
              'gvn': 'Global value numbering',
              'loop-simplify': 'Canonicalize natural loops'
            },
            optimization_levels: {
              '-O0': 'No optimization',
              '-O1': 'Basic optimization',
              '-O2': 'Moderate optimization',
              '-O3': 'Aggressive optimization'
            }
          });
          
          setSystemData({
            tools_available: {
              'clang': true,
              'opt': true,
              'llc': true,
              'riscv64-gcc': true,
              'qemu-riscv64': true
            },
            all_tools_ready: true,
            target_architecture: 'RISC-V 64-bit'
          });
        } else {
          setError('Backend not available. Start the backend to see live analytics.');
        }
      } catch (err) {
        setError('Backend not available. Start the backend with: python3 app_simplified.py');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <Layout>
        <main className="min-h-screen p-8 flex items-center justify-center">
          <div className="text-center">
            <Spinner />
            <p className="text-white mt-4">Loading analytics...</p>
          </div>
        </main>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <main className="min-h-screen p-8 max-w-6xl mx-auto">
          <div className="glass-card p-8 rounded-2xl text-center">
            <h2 className="text-2xl font-bold text-red-400 mb-4">Error</h2>
            <p className="text-white/80">{error}</p>
          </div>
        </main>
      </Layout>
    );
  }

  return (
    <Layout>
      <main className="min-h-screen p-8 max-w-6xl mx-auto">
        <h1 className="text-5xl font-bold mb-12 text-center text-white drop-shadow-lg animate-fade-in">
          Analytics Dashboard
        </h1>

        {/* System Status Overview */}
        <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
          <h2 className="text-3xl font-bold text-white mb-6">System Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="glass p-6 rounded-xl">
              <p className="text-white/70 text-sm mb-2">Status</p>
              <p className={`text-2xl font-bold ${systemData?.all_tools_ready ? 'text-green-400' : 'text-yellow-400'}`}>
                {systemData?.all_tools_ready ? '✓ Ready' : '⚠ Partial'}
              </p>
            </div>
            <div className="glass p-6 rounded-xl">
              <p className="text-white/70 text-sm mb-2">Target Architecture</p>
              <p className="text-2xl font-bold text-purple-400">
                {systemData?.target_architecture || 'Unknown'}
              </p>
            </div>
            <div className="glass p-6 rounded-xl">
              <p className="text-white/70 text-sm mb-2">Models Available</p>
              <p className="text-2xl font-bold text-blue-400">
                {modelsData?.total_available || 0}
              </p>
            </div>
            <div className="glass p-6 rounded-xl">
              <p className="text-white/70 text-sm mb-2">Total Features</p>
              <p className="text-2xl font-bold text-pink-400">
                {featuresData?.total_features || 0}
              </p>
            </div>
          </div>
        </section>

        {/* Models Information */}
        <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
          <h2 className="text-3xl font-bold text-white mb-6">ML Models</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Transformer Model */}
            <div className="glass p-6 rounded-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-white">Transformer</h3>
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                  modelsData?.models?.transformer?.available 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {modelsData?.models?.transformer?.available ? 'Available' : 'Unavailable'}
                </span>
              </div>
              {modelsData?.models?.transformer?.available && (
                <dl className="space-y-2 text-sm">
                  <div>
                    <dt className="text-white/70">Device</dt>
                    <dd className="text-white font-medium">{modelsData.models.transformer.device}</dd>
                  </div>
                  <div>
                    <dt className="text-white/70">Vocabulary Size</dt>
                    <dd className="text-white font-medium">{modelsData.models.transformer.vocab_size}</dd>
                  </div>
                  <div>
                    <dt className="text-white/70">Features</dt>
                    <dd className="text-white font-medium">{modelsData.models.transformer.num_features}</dd>
                  </div>
                </dl>
              )}
            </div>

            {/* XGBoost Model */}
            <div className="glass p-6 rounded-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-white">XGBoost</h3>
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${
                  modelsData?.models?.xgboost?.available 
                    ? 'bg-green-500/20 text-green-400' 
                    : 'bg-red-500/20 text-red-400'
                }`}>
                  {modelsData?.models?.xgboost?.available ? 'Available' : 'Unavailable'}
                </span>
              </div>
              {!modelsData?.models?.xgboost?.available && (
                <p className="text-white/60 text-sm">Model not found. Train the model to enable XGBoost predictions.</p>
              )}
            </div>
          </div>
        </section>

        {/* Feature Extraction */}
        <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
          <h2 className="text-3xl font-bold text-white mb-6">Feature Extraction</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <div className="glass p-6 rounded-xl">
              <h3 className="text-xl font-bold text-white mb-2">Extraction Method</h3>
              <p className="text-white/80">{featuresData?.extraction_method}</p>
            </div>
            <div className="glass p-6 rounded-xl">
              <h3 className="text-xl font-bold text-white mb-2">Total Features</h3>
              <p className="text-3xl font-bold text-blue-400">{featuresData?.total_features}</p>
            </div>
          </div>
          
          {featuresData?.feature_categories && (
            <div>
              <h3 className="text-xl font-bold text-white mb-4">Feature Categories</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(featuresData.feature_categories).map(([category, description]) => (
                  <div key={category} className="glass p-4 rounded-xl hover:bg-white/15">
                    <h4 className="text-white font-bold capitalize mb-1">{category}</h4>
                    <p className="text-white/70 text-sm">{description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* LLVM Passes */}
        <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
          <h2 className="text-3xl font-bold text-white mb-6">LLVM Optimization Passes</h2>
          <div className="mb-6">
            <p className="text-white/80 text-lg">
              Total available passes: <span className="font-bold text-white">{passesData?.total_passes}</span>
            </p>
          </div>
          
          {passesData?.common_passes && (
            <div className="mb-8">
              <h3 className="text-xl font-bold text-white mb-4">Common Passes</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(passesData.common_passes).slice(0, 10).map(([pass, description]) => (
                  <div key={pass} className="glass p-4 rounded-xl hover:bg-white/15 transition-all">
                    <h4 className="text-white font-bold font-mono mb-1">{pass}</h4>
                    <p className="text-white/70 text-sm">{description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {passesData?.optimization_levels && (
            <div>
              <h3 className="text-xl font-bold text-white mb-4">Standard Optimization Levels</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(passesData.optimization_levels).map(([level, description]) => (
                  <div key={level} className="glass p-4 rounded-xl text-center hover:bg-white/15 transition-all hover:scale-105">
                    <p className="text-2xl font-bold text-white mb-2">{level}</p>
                    <p className="text-white/70 text-sm">{description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* System Tools */}
        <section className="glass-card p-8 rounded-2xl mb-8 animate-slide-in">
          <h2 className="text-3xl font-bold text-white mb-6">System Tools</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {systemData?.tools_available && Object.entries(systemData.tools_available).map(([tool, available]) => (
              <div key={tool} className="glass p-4 rounded-xl text-center">
                <div className={`text-3xl mb-2 ${available ? 'text-green-400' : 'text-red-400'}`}>
                  {available ? '✓' : '✗'}
                </div>
                <p className="text-white font-medium text-sm">{tool}</p>
              </div>
            ))}
          </div>
          
          {systemData?.versions && Object.keys(systemData.versions).length > 0 && (
            <div className="mt-6">
              <h3 className="text-xl font-bold text-white mb-4">Tool Versions</h3>
              <div className="space-y-2">
                {Object.entries(systemData.versions).map(([tool, version]) => (
                  <div key={tool} className="glass p-3 rounded-xl flex justify-between items-center">
                    <span className="text-white font-medium">{tool}</span>
                    <span className="text-white/70 font-mono text-sm">{version}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Architecture Info */}
        <section className="glass-card p-8 rounded-2xl animate-slide-in">
          <h2 className="text-3xl font-bold text-white mb-6">Target Architecture</h2>
          <div className="glass p-6 rounded-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold text-white mb-2">RISC-V</h3>
                <p className="text-white/80">
                  All compilation and optimization targets <span className="font-bold text-purple-400">{featuresData?.target_architecture}</span> architecture
                </p>
              </div>
              <div className="text-6xl">🔧</div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
