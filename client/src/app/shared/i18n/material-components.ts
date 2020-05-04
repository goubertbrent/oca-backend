import { Provider } from '@angular/core';
import { MatPaginatorIntl } from '@angular/material/paginator';
import { TranslateService } from '@ngx-translate/core';
import { Subject } from 'rxjs';

export class MatPaginatorIntlImpl implements MatPaginatorIntl {
  readonly changes = new Subject<void>();
  firstPageLabel: string;
  itemsPerPageLabel: string;
  lastPageLabel: string;
  nextPageLabel: string;
  previousPageLabel: string;

  constructor(private translate: TranslateService) {
    const keys = ['oca.first_page', 'oca.items_per_page', 'oca.last_page', 'oca.next_page', 'oca.previous_page'];
    translate.get(keys).subscribe(results => {
      this.firstPageLabel = results[ keys[ 0 ] ];
      this.itemsPerPageLabel = results[ keys[ 1 ] ];
      this.lastPageLabel = results[ keys[ 2 ] ];
      this.nextPageLabel = results[ keys[ 3 ] ];
      this.previousPageLabel = results[ keys[ 4 ] ];
      this.changes.next();
    });
  }

  getRangeLabel(page: number, pageSize: number, length: number): string {
    let fromUntil: string;
    if (page === 0 && length === 0) {
      fromUntil = '0 – 0';
    } else {

      length = Math.max(length, 0);
      const startIndex = page * pageSize;

      // If the start index exceeds the list length, do not try and fix the end index to the end.
      const endIndex = startIndex < length ?
        Math.min(startIndex + pageSize, length) :
        startIndex + pageSize;
      fromUntil = `${startIndex + 1} – ${endIndex}`;
    }
    return this.translate.instant('oca.page_results_of_total', { page: fromUntil, length });
  }

}

export const MAT_PAGINATOR_INTL_PROVIDER: Provider = {
  provide: MatPaginatorIntl,
  deps: [TranslateService],
  useClass: MatPaginatorIntlImpl,
};
