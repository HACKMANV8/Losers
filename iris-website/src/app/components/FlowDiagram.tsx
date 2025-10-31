'use client';

const FlowDiagram = () => {
  return (
    <div className="flex items-center justify-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
      <div className="flex flex-col items-center">
        <div className="p-4 bg-gray-200 dark:bg-gray-700 rounded-lg">Source Code</div>
      </div>
      <div>&rarr;</div>
      <div className="flex flex-col items-center">
        <div className="p-4 bg-gray-200 dark:bg-gray-700 rounded-lg">LLVM IR</div>
      </div>
      <div>&rarr;</div>
      <div className="flex flex-col items-center">
        <div className="p-4 bg-gray-200 dark:bg-gray-700 rounded-lg">Feature Extraction</div>
      </div>
      <div>&rarr;</div>
      <div className="flex flex-col items-center">
        <div className="p-4 bg-indigo-200 dark:bg-indigo-700 rounded-lg">ML Model</div>
      </div>
      <div>&rarr;</div>
      <div className="flex flex-col items-center">
        <div className="p-4 bg-gray-200 dark:bg-gray-700 rounded-lg">Pass Sequence</div>
      </div>
      <div>&rarr;</div>
      <div className="flex flex-col items-center">
        <div className="p-4 bg-green-200 dark:bg-green-700 rounded-lg">Optimized Binary</div>
      </div>
    </div>
  );
};

export default FlowDiagram;
