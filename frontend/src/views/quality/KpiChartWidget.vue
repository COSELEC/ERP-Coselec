<script setup lang="ts">
import { computed } from 'vue';
import type { KPIIndicator } from '@/services/kpi';
import VueApexCharts from "vue3-apexcharts";

const formatKpiValue = (val: number, targetRaw?: string | null) => {
  if (val === null || val === undefined) return '';
  const hasPercent = targetRaw?.includes('%');
  
  // Appliquer le formatage en pourcentage pour toute valeur entre 0 et 1 inclus
  const isFraction = val >= 0 && val <= 1;
  
  if (hasPercent || isFraction) {
    const displayVal = (val >= 0 && val <= 1) ? Number((val * 100).toFixed(1)) : val;
    return `${displayVal}%`;
  }
  return val;
};

const props = defineProps<{
  indicator: KPIIndicator;
  year: number;
}>();

const monthNames = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'];

const targetConfig = computed(() => {
  return props.indicator.yearly_targets.find(t => t.year === props.year);
});

const chartSeries = computed(() => {
  const data = new Array(12).fill(null);
  
  props.indicator.values.forEach(v => {
    if (v.year === props.year && v.month >= 1 && v.month <= 12) {
      data[v.month - 1] = v.value_numeric;
    }
  });

  return [{
    name: props.indicator.name,
    data: data
  }];
});

const getColors = computed(() => {
  const data = chartSeries.value[0].data;
  const target = targetConfig.value;
  
  if (!target || target.target_numeric === null || target.operator === null) {
    return data.map(() => '#3b82f6'); 
  }

  return data.map(val => {
    if (val === null) return '#d1d5db'; 
    
    let isSuccess = false;
    
    switch (target.operator) {
      case 'GTE':
        isSuccess = val >= target.target_numeric!;
        break;
      case 'LTE':
        isSuccess = val <= target.target_numeric!;
        break;
      case 'BETWEEN':
        if (target.target_numeric_max !== null) {
          isSuccess = val >= target.target_numeric! && val <= target.target_numeric_max!;
        }
        break;
      case 'EQ':
        isSuccess = val === target.target_numeric!;
        break;
    }
    
    return isSuccess ? '#10b981' : '#ef4444'; 
  });
});

const chartOptions = computed(() => {
  const annotations: any = { yaxis: [] };
  const target = targetConfig.value;
  
  if (target && target.target_numeric !== null) {
    annotations.yaxis.push({
      y: target.target_numeric,
      y2: target.target_numeric_max, 
      borderColor: '#d10f2f',
      fillColor: target.operator === 'BETWEEN' ? '#d10f2f' : undefined,
      opacity: 0.2,
      label: {
        borderColor: '#d10f2f',
        style: {
          color: '#fff',
          background: '#d10f2f',
        },
        text: `Cible: ${target.target_raw || target.target_numeric}`
      }
    });
  }

  return {
    chart: {
      type: 'bar',
      height: 250,
      toolbar: { show: false },
      animations: { enabled: true }
    },
    plotOptions: {
      bar: {
        borderRadius: 4,
        columnWidth: '60%',
        distributed: true 
      }
    },
    colors: getColors.value,
    dataLabels: {
      enabled: true,
      formatter: function (val: number) {
        return formatKpiValue(val, target?.target_raw);
      },
      style: {
        fontSize: '10px',
      }
    },
    xaxis: {
      categories: monthNames,
      labels: {
        style: { colors: '#6b7280', fontSize: '11px' }
      }
    },
    yaxis: {
      labels: {
        formatter: function (val: number) {
          return formatKpiValue(val, target?.target_raw);
        },
        style: { colors: '#6b7280' }
      }
    },
    grid: {
      borderColor: '#f3f4f6',
      strokeDashArray: 4,
    },
    legend: { show: false },
    annotations: annotations,
    tooltip: {
      y: {
        formatter: function (val: number) {
          return formatKpiValue(val, target?.target_raw);
        }
      }
    }
  };
});
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
    <div class="flex justify-between items-start mb-4">
      <div>
        <h4 class="font-semibold text-gray-900 text-sm mb-1 leading-tight">{{ indicator.name }}</h4>
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
            Fréquence: {{ targetConfig?.frequency || 'N/A' }}
          </span>
          <span v-if="targetConfig?.target_raw" class="text-xs font-medium text-[#d10f2f] bg-red-50 border border-red-100 px-2 py-0.5 rounded">
            Cible: {{ targetConfig.target_raw }}
          </span>
        </div>
      </div>
    </div>
    
    <VueApexCharts 
      type="bar" 
      height="250" 
      :options="chartOptions" 
      :series="chartSeries" 
    />
  </div>
</template>
