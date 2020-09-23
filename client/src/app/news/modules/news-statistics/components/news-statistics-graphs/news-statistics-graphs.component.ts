import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { ChartType } from 'angular-google-charts';
import { NewsItemBasicStatistics, NewsItemTimeStatistics } from '../../../../news';

export type PossibleMetrics = Exclude<keyof NewsItemBasicStatistics, 'id'>;

@Component({
  selector: 'oca-news-statistics-graphs',
  templateUrl: './news-statistics-graphs.component.html',
  styleUrls: ['./news-statistics-graphs.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsStatisticsGraphsComponent implements OnChanges {
  @Input() basicStatistics: NewsItemBasicStatistics;
  @Input() timeStatistics: NewsItemTimeStatistics | null;
  @Input() selectedMetric: PossibleMetrics = 'reached';

  possibleMetrics: { value: PossibleMetrics, label: string }[] = [
    { value: 'reached', label: 'oca.reached' },
    { value: 'action', label: 'oca.action' },
  ];

  genderMapping: { [ key: string ]: string } = {};
  charts: {
    age: any;
    gender: any;
    time: any;
  };
  hasData = true;

  constructor(private translate: TranslateService) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if ((changes.timeStatistics || changes.selectedMetric) && this.timeStatistics) {
      this.genderMapping = {
        female: this.translate.instant('oca.gender-female'),
        male: this.translate.instant('oca.gender-male'),
        unknown: this.translate.instant('oca.unknown'),
      };
      this.createChartData();
    }
  }

  createChartData() {
    if (!this.timeStatistics) {
      return;
    }
    this.createCharts();
  }

  updateCurrentMetric(metric: PossibleMetrics) {
    this.selectedMetric = metric;
    this.createChartData();
  }

  private createCharts() {
    if (!this.timeStatistics || this.timeStatistics.reached.length === 0) {
      this.hasData = false;
      return;
    } else {
      this.hasData = true;
    }
    const amountStr = this.translate.instant('oca.amount');
    const metric = this.possibleMetrics.find(m => m.value === this.selectedMetric);
    const lineTitle = this.translate.instant(metric ? metric.label : 'oca.reached');
    const selectedBasicStats = this.basicStatistics[ this.selectedMetric ];
    const timeStats = this.timeStatistics[ this.selectedMetric ].map(item => ([new Date(item.time), item.value]));
    this.charts = {
      age: {
        chartType: ChartType.ColumnChart,
        // Remove 'unknown' from age graph
        dataTable: selectedBasicStats.age.slice(1, selectedBasicStats.age.length).map(v => ([v.key, v.value])),
        columnNames: [this.translate.instant('oca.gender'), amountStr],
        options: {
          title: `${this.translate.instant('oca.age')} (${selectedBasicStats.age[ 0 ].value} ${this.translate.instant('oca.unknown').toLowerCase()})`,
          legend: {
            position: 'none',
          },
          width: 600,
          height: 300,
          backgroundColor: 'transparent',
          hAxis: {
            showTextEvery: 3,
          },
          isStacked: true,
          animation: { duration: 1000, easing: 'out', startup: true },
        },
      },
      gender: {
        chartType: ChartType.PieChart,
        dataTable: selectedBasicStats.gender.map(i => ([this.genderMapping[ i.key ], i.value])),
        columnNames: [this.translate.instant('oca.gender'), amountStr],
        options: {
          title: this.translate.instant('oca.gender'),
          width: 300,
          height: 300,
          backgroundColor: 'transparent',
          legend: {
            position: 'bottom',
          },
        },
      },
      time: {
        chartType: ChartType.LineChart,
        dataTable: timeStats,
        columnNames: [this.translate.instant('oca.Date'), amountStr],
        options: {
          title: lineTitle,
          width: 900,
          height: 300,
          backgroundColor: 'transparent',
          explorer: {
            actions: ['dragToZoom', 'rightClickToReset'],
            axis: 'horizontal',
            keepInBounds: true,
            maxZoomIn: 0.1,
          },
          legend: { position: 'none' },
          animation: { duration: 1000, easing: 'out', startup: true },
        },
      },
    };
  }

  private getAgeLabel(age: string) {
    return age === '0 - 5' ? this.translate.instant('oca.unknown') : age;
  }
}
