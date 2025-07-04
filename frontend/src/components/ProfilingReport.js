import React from 'react';
import ReactECharts from 'echarts-for-react';

const ProfilingReport = ({ report }) => {
  if (!report || !report.variables) {
    return <p>No report data available to display.</p>;
  }

  // --- Prepare data for ECharts ---
  // We will create a bar chart to show the percentage of missing values for each variable.
  const variables = Object.keys(report.variables);
  const missingPercentage = variables.map(
    (key) => report.variables[key]['p_missing'] * 100
  );

  const chartOption = {
    title: {
      text: 'Percentage of Missing Values per Variable',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
      formatter: '{b}: {c:.2f}% missing',
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      boundaryGap: [0, 0.01],
      axisLabel: {
        formatter: '{value}%'
      }
    },
    yAxis: {
      type: 'category',
      data: variables.map(v => v.length > 20 ? v.substring(0, 20) + '...' : v), // Truncate long names
      inverse: true
    },
    series: [
      {
        name: 'Missing %',
        type: 'bar',
        data: missingPercentage,
      },
    ],
  };

  return (
    <div style={{ marginTop: '20px' }}>
      <h3>Data Profiling Report</h3>
      <ReactECharts option={chartOption} style={{ height: '400px', width: '100%' }} />
      {/* We can add more charts and tables here to render other parts of the report */}
    </div>
  );
};

export default ProfilingReport; 