import { ChangeDetectionStrategy, Component, Input, OnChanges, SimpleChange, ViewEncapsulation } from '@angular/core';
import { PageEvent } from '@angular/material/paginator';
import { Chart } from '../../reports';

@Component({
  selector: 'oca-paginated-charts',
  templateUrl: './paginated-charts.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
  encapsulation: ViewEncapsulation.None,
})
export class PaginatedChartsComponent implements OnChanges {
  @Input() charts: Chart[] = [];
  selectedIndex = 0;
  pageLength = 0;

  ngOnChanges(changes: { [P in keyof this]: SimpleChange }): void {
    if (changes.charts) {
      this.selectedIndex = 0;
      this.pageLength = this.charts ? this.charts.length : 0;
    }
  }

  onPageChanged($event: PageEvent) {
    this.selectedIndex = $event.pageIndex;
  }
}
