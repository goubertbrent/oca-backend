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
  chart: { data: (string | number)[][]; columns: string[]; options: google.visualization.BarChartOptions; type: string };
  circles: { lat: number; lon: number; radius: number }[];
  displayedColumns = ['name', 'amount', 'formatted_address'];
  dataSource = new MatTableDataSource();
  openInfoWindows: { [ key: string ]: boolean } = {};

  private previousInfoWindow: AgmInfoWindow | null = null;
  private RADIUS_MULTIPLIER = 200;  // Biggest circle will be 200m

  ngOnChanges(changes: SimpleChanges): void {
    if (changes.statistics && this.statistics.data) {
      const merchants = this.statistics.data.results
        .filter(m => m.total > 0)
        .sort((first, second) => second.total - first.total);
      this.createChart(merchants, 10);
      this.createCircles(merchants);
      this.openInfoWindows = {};
      for (const merchant of merchants) {
        this.openInfoWindows[ merchant.id ] = false;
      }
      this.dataSource.data = merchants;
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

  private createChart(merchants: MerchantStatistics[], amount: number) {
    const chartData = merchants.slice(0, amount).map(m => ([m.name, m.total]));
    this.chart = {
      type: 'BarChart',
      columns: ['Name', ''],
      data: chartData,
      options: {
        width: this.container.nativeElement.offsetWidth - 80,
        height: 300,
        legend: { position: 'none' },
        backgroundColor: 'transparent',
        vAxis: { textStyle: { fontSize: 12 } },
        chartArea: { height: 260, bottom: 32, right: 64 },
      },
    };
  }

  private createCircles(merchants: MerchantStatistics[]) {
    const max = merchants[ 0 ].total;
    this.circles = merchants.map(merchant => ({
      lat: merchant.location.lat,
      lon: merchant.location.lon,
      radius: this.getCircleRadius(max, merchant.total),
    }));
  }

  private getCircleRadius(maximumAmount: number, amount: number) {
    return Math.max(amount / maximumAmount * this.RADIUS_MULTIPLIER);
  }

  rowClicked(row: MerchantStatistics) {
    for (const merchantId of Object.keys(this.openInfoWindows)) {
      this.openInfoWindows[ merchantId ] = false;
    }
    this.openInfoWindows[ row.id ] = true;
  }
}
