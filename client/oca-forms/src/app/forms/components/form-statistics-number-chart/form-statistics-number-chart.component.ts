import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges, ViewEncapsulation } from '@angular/core';
import { ValueAmount } from '../../interfaces/forms.interfaces';

@Component({
  selector: 'oca-form-statistics-number-chart',
  templateUrl: './form-statistics-number-chart.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class FormStatisticsNumberChartComponent implements OnChanges {
  @Input() values: ValueAmount[];
  chart: { data: (string | number)[][]; columns: string[]; options: any; type: string };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.values && changes.values.currentValue) {
      this.chart = this.getChart(changes.values.currentValue);
    }
  }

  getChart(values: ValueAmount[]) {
    return {
      type: 'BarChart',
      columns: [ 'Value', '' ],
      data: values.map(value => ([ value.value, value.amount ])),
      options: {
        width: 700,
        height: Math.max(150, values.length * 30),
        legend: { position: 'none' },
        backgroundColor: 'transparent',
        bars: 'horizontal', // Required for Material Bar Charts.
        vAxis: { textStyle: { fontSize: '12', paddingRight: '200', marginRight: '200' } },
        chartArea: { left: '25%', top: 0, bottom: '20px' },  // bottom padding for x axis
      },
    };
  }
}
