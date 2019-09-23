import { AgmInfoWindow } from '@agm/core';
import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  OnInit,
  Output,
  QueryList,
  SimpleChanges,
  ViewChild,
  ViewChildren,
} from '@angular/core';
import { MatTableDataSource } from '@angular/material';
import { MatPaginator } from '@angular/material/paginator';
import { MatSort } from '@angular/material/sort';
import { Loadable } from '../../../shared/loadable/loadable';
import { MerchantStatistics, ProjectStatistics } from '../../projects';

interface MapCircle {
  lat: number;
  lon: number;
  radius: number;
}

interface ChartOptions {
  data: (string | number)[][];
  columns: string[];
  options: google.visualization.BarChartOptions;
  type: string
}

@Component({
  selector: 'oca-project-statistics',
  templateUrl: './project-statistics.component.html',
  styleUrls: [ './project-statistics.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProjectStatisticsComponent implements OnInit, OnChanges {
  @ViewChild('container', { static: true }) container: ElementRef<HTMLDivElement>;
  @ViewChild(MatSort, { static: true }) sort: MatSort;
  @ViewChild(MatPaginator, { static: true }) paginator: MatPaginator;
  @ViewChildren(AgmInfoWindow) infoWindows: QueryList<ElementRef<AgmInfoWindow>>;
  @Input() statistics: Loadable<ProjectStatistics>;
  @Output() loadMore = new EventEmitter();
  chart: ChartOptions | null = null;
  circles: MapCircle[];
  displayedColumns = ['name', 'amount', 'formatted_address'];
  dataSource = new MatTableDataSource();
  openInfoWindows: { [ key: string ]: boolean } = {};

  private previousInfoWindow: AgmInfoWindow | null = null;
  private MAX_CIRCLE_RADIUS = 200;  // Biggest circle will be 200m

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.statistics && this.statistics.data) {
      this.openInfoWindows = {};
      if (this.statistics.data.results.length > 0) {
        const merchants = this.statistics.data.results
          .filter(m => m.total > 0)
          .sort((first, second) => second.total - first.total);
        this.chart = this.createChart(merchants, 10);
        this.circles = this.createCircles(merchants);
        for (const merchant of merchants) {
          this.openInfoWindows[ merchant.id ] = false;
        }
        this.dataSource.data = merchants;
      } else {
        this.clear();
      }
    }
  }

  ngOnInit(): void {
    this.sort.active = 'total';
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
  }

  markerClicked(infoWindow: AgmInfoWindow) {
    if (this.previousInfoWindow) {
      this.previousInfoWindow.close();
    }
    this.previousInfoWindow = infoWindow;
  }

  private clear() {
    this.dataSource.data = [];
    this.chart = null;
    this.circles = [];
  }

  private createChart(merchants: MerchantStatistics[], amount: number): ChartOptions {
    const chartData = merchants.slice(0, amount).map(m => ([m.name, m.total]));
    return {
      type: 'BarChart',
      columns: ['Name', ''],
      data: chartData,
      options: {
        width: this.container.nativeElement.offsetWidth - 80,
        height: chartData.length > 3 ? 300 : 150,
        legend: { position: 'none' },
        backgroundColor: 'transparent',
        vAxis: { textStyle: { fontSize: 12 } },
        chartArea: { height: 260, bottom: 32, right: 64 },
      },
    };
  }

  private createCircles(merchants: MerchantStatistics[]): MapCircle[] {
    const max = merchants[ 0 ].total;
    return merchants.map(merchant => ({
      lat: merchant.location.lat,
      lon: merchant.location.lon,
      radius: this.getCircleRadius(max, merchant.total),
    }));
  }

  private getCircleRadius(maximumAmount: number, amount: number) {
    return Math.max(amount / maximumAmount * this.MAX_CIRCLE_RADIUS);
  }

  rowClicked(row: MerchantStatistics) {
    for (const merchantId of Object.keys(this.openInfoWindows)) {
      this.openInfoWindows[ merchantId ] = false;
    }
    this.openInfoWindows[ row.id ] = true;
  }
}
