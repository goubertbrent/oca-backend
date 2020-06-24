import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { ChartBase, ChartType } from 'angular-google-charts';
import { NewsApp, NewsItemAppStatistics, NewsItemStatistics } from '../../../../interfaces';

interface Stats {
  appId: string;
  age: [ string, number ][];
  gender: [ string, number ][];
  time: [ Date, number ][];
  total: number;
}

interface KV {
  [ key: string ]: number;
}

interface Mapping {
  gender: KV;
  age: KV;
  time: KV;
}

export type PossibleMetrics = Exclude<keyof NewsItemAppStatistics, 'app_id'>;

@Component({
  selector: 'oca-news-statistics-graphs',
  templateUrl: './news-statistics-graphs.component.html',
  styleUrls: [ './news-statistics-graphs.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class NewsStatisticsGraphsComponent implements OnChanges {
  @Input() newsStatistics: NewsItemStatistics | null;
  @Input() apps: NewsApp[];
  @Input() selectedMetric: PossibleMetrics = 'reached';

  possibleMetrics: { value: PossibleMetrics, label: string }[] = [
    { value: 'reached', label: 'oca.reached' },
    { value: 'rogered', label: 'oca.rogered' },
    { value: 'action', label: 'oca.action' },
    { value: 'followed', label: 'oca.followed' },
  ];

  selectedApp = 'all';
  currentStats: Stats | null;
  appNameMapping: { [ key: string ]: string };
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
    if ((changes.newsStatistics || changes.selectedMetric) && this.newsStatistics) {
      this.genderMapping = {
        'gender-female': this.translate.instant('oca.gender-female'),
        'gender-male': this.translate.instant('oca.gender-male'),
        unknown: this.translate.instant('oca.unknown'),
      };
      this.appNameMapping = {};
      for (const app of this.apps) {
        this.appNameMapping[ app.id ] = app.name;
      }
      this.createChartData();
    }
  }

  createChartData() {
    if(!this.newsStatistics){
      return;
    }
    if (this.selectedApp === 'all') {
      this.currentStats = getTotalStats(this.newsStatistics.details, this.selectedMetric);
    } else {
      const stats = this.newsStatistics.details.find(s => s.app_id === this.selectedApp);
      if (stats) {
        this.currentStats = getStats(stats, this.selectedMetric);
      } else {
        this.currentStats = null;
      }
    }
    this.createCharts();
  }

  updateCurrentMetric(metric: PossibleMetrics) {
    this.selectedMetric = metric;
    this.createChartData();
  }

  private createCharts() {
    const appChartData = this.currentStats;
    if (!appChartData || !(appChartData.time.length)) {
      this.hasData = false;
      return;
    } else {
      this.hasData = true;
    }
    const amountStr = this.translate.instant('oca.amount');
    const metric = this.possibleMetrics.find(m => m.value === this.selectedMetric);
    const lineTitle = this.translate.instant(metric ? metric.label : 'oca.reached');
    this.charts = {
      age: {
        chartType: ChartType.ColumnChart,
        dataTable: appChartData.age.map(i => [ i[ 0 ] === '0 - 5' ? this.translate.instant('oca.unknown') : i[ 0 ], i[ 1 ] ]),
        columnNames: [ this.translate.instant('oca.gender'), amountStr ],
        options: {
          title: this.translate.instant('oca.age'),
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
        dataTable: appChartData.gender.map(item => [ this.genderMapping[ item[ 0 ] ], item[ 1 ] ]),
        columnNames: [ this.translate.instant('oca.gender'), amountStr ],
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
        dataTable: appChartData.time,
        columnNames: [ this.translate.instant('oca.Date'), amountStr ],
        options: {
          title: lineTitle,
          width: 900,
          height: 300,
          backgroundColor: 'transparent',
          explorer: {
            actions: [ 'dragToZoom', 'rightClickToReset' ],
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
}

function getTotalStats(stats: NewsItemAppStatistics[], metric: PossibleMetrics) {
  const result: Stats = {
    appId: 'all',
    age: [],
    gender: [],
    time: [],
    total: 0,
  };
  const props: (Exclude<keyof Mapping, 'time' | 'total'>)[] = [ 'age', 'gender' ];
  const mappings: Mapping = {
    gender: {},
    age: {},
    time: {},
  };
  for (const appStats of stats) {
    const stat = appStats[ metric ];
    result.total += stat.total;
    for (const prop of props) {
      for (const val of stat[ prop ]) {

        if (val.key in mappings[ prop ]) {
          mappings[ prop ][ val.key ] += val.value;
        } else {
          mappings[ prop ][ val.key ] = val.value;
        }
      }
    }
    for (const val of stat.time) {
      if (val.timestamp in mappings.time) {
        mappings.time[ val.timestamp ] += val.amount;
      } else {
        mappings.time[ val.timestamp ] = val.amount;
      }
    }
  }
  result.gender = mapToArray(mappings.gender);
  result.age = mapToArray(mappings.age);
  result.time = mapToDateArray(mappings.time);
  return result;
}

function mapToArray(values: KV): [ string, number ][] {
  return Object.keys(values).map(key => [ key, values[ key ] ] as [ string, number ]);
}

function mapToDateArray(values: KV) {
  const temp = Object.keys(values).map(key => [ new Date(parseInt(key, 10) * 1000), values[ key ] ] as [ Date, number ]);
  let previous = 0;
  for (const item of temp) {
    item[ 1 ] = previous + item[ 1 ];
    previous = item[ 1 ];
  }
  return temp;
}

function getStats(stats: NewsItemAppStatistics, metric: PossibleMetrics) {
  const result: Stats = {
    appId: stats.app_id,
    age: [],
    gender: [],
    time: [],
    total: 0,
  };
  const stat = stats[ metric ];
  result.total = stat.total;
  for (const age of stat.age) {
    result.age.push([ age.key, age.value ]);
  }
  for (const gender of stat.gender) {
    result.gender.push([ gender.key, gender.value ]);
  }
  for (let i = 0; i < stat.time.length; i++) {
    const timeStat = stat.time[ i ];
    // Cumulative sum
    const amount = (i === 0 ? 0 : result.time[ i - 1 ][ 1 ]) + timeStat.amount;
    result.time.push([ new Date(timeStat.timestamp * 1000), amount ]);
  }
  return result;
}
