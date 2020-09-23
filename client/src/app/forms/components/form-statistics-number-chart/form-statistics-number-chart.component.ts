import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges, ViewEncapsulation } from '@angular/core';
import { ChartType } from 'angular-google-charts';
import { ValueAmount } from '../../interfaces/forms';

@Component({
  selector: 'oca-form-statistics-number-chart',
  templateUrl: './form-statistics-number-chart.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class FormStatisticsNumberChartComponent implements OnChanges {
  @Input() values: ValueAmount[];
  chart: { data: (string | number)[][]; columns: string[]; options: google.visualization.BarChartOptions; type: ChartType };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.values && changes.values.currentValue) {
      this.chart = this.getChart(changes.values.currentValue);
    }
  }

  getChart(values: ValueAmount[]) {
    return {
      type: ChartType.BarChart,
      columns: ['Value', ''],
      data: values.map(value => ([value.value, value.amount])),
      options: {
        width: 600,
        height: Math.max(150, values.length * 30),
        legend: 'none' as 'none',  // not sure why but without the 'as' it errors
        backgroundColor: 'transparent',
        bars: 'horizontal', // Required for Material Bar Charts.
        vAxis: { textStyle: { fontSize: 12, paddingRight: '200', marginRight: '200' } },
        chartArea: { left: '25%', top: 0, bottom: '0px' },  // bottom padding for x axis
      },
    };
  }
}
