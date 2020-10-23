import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { MatSort, Sort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { select, Store } from '@ngrx/store';
import { TranslateService } from '@ngx-translate/core';
import { Observable, Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { isShopUser } from '../../shared/shared.state';
import { VoucherService, VouchersServiceList } from '../vouchers';
import { GetServicesAction, WhitelistVoucherServiceAction } from '../vouchers.actions';
import { getVoucherList, getVoucherServices, voucherServicesLoading } from '../vouchers.selectors';
import { WhitelistDialogComponent, WhitelistDialogData, WhitelistDialogResult } from './whitelist-dialog.component';

@Component({
  selector: 'oca-vouchers-page',
  templateUrl: './vouchers-page.component.html',
  styleUrls: ['./vouchers-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VouchersPageComponent implements OnInit, OnDestroy {
  @ViewChild(MatSort) sort: MatSort;

  displayedColumns: (keyof VoucherService)[] = ['name', 'email', 'creation_date', 'address', 'whitelist_date', 'merchant_registered'];
  loading$: Observable<boolean>;
  isShopUser$: Observable<boolean>;
  voucherList$: Observable<VouchersServiceList>;
  dataSource = new MatTableDataSource<VoucherService>();
  allServices: VoucherService[];

  private destroyed$ = new Subject();

  constructor(private translate: TranslateService,
              private matDialog: MatDialog,
              private store: Store<any>) {
  }

  ngOnInit(): void {
    this.dataSource.sort = this.sort;
    this.store.pipe(select(getVoucherServices), takeUntil(this.destroyed$)).subscribe(services => {
      this.allServices = services;
      const data = this.allServices.slice();
      this.dataSource.data = data.sort((a, b) => {
        return compare(a.creation_date, b.creation_date, false);
      });
    });
    this.getServices();
    this.voucherList$ = this.store.pipe(select(getVoucherList));
    this.loading$ = this.store.pipe(select(voucherServicesLoading));
    this.isShopUser$ = this.store.pipe(select(isShopUser));
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  applyFilter(filterValue: string) {
    this.dataSource.filter = filterValue?.trim().toLowerCase() ?? '';
  }

  refresh() {
    this.getServices();
  }

  sortData(sort: Sort) {
    const data = this.allServices.slice();
    if (!sort.active || sort.direction === '') {
      this.dataSource.data = data;
      return;
    }

    this.dataSource.data = data.sort((a, b) => {
      const isAsc = sort.direction === 'asc';
      switch (sort.active) {
        case 'name':
          return compare(a.name, b.name, isAsc);
        case 'email':
          return compare(a.email, b.email, isAsc);
        case 'creation_date':
          return compare(a.creation_date, b.creation_date, isAsc);
        default:
          return 0;
      }
    });
  }

  whitelistService(row: VoucherService) {
    const message = `${this.translate.instant('oca.reservation-name')}: ${row.name}
  ${this.translate.instant('oca.Email')}: ${row.email}
  ${this.translate.instant('oca.address')}: ${row.address}`;
    const data: WhitelistDialogData = {
      title: this.translate.instant('oca.whitelist'),
      message,
      yes: this.translate.instant('oca.reservation-approve'),
      no: this.translate.instant('oca.reservation-decline'),
      cancel: this.translate.instant('oca.Cancel'),
    };
    const dialog = this.matDialog.open(WhitelistDialogComponent, { data });
    dialog.afterClosed().subscribe((result?: WhitelistDialogResult) => {
      if (!result?.action) {
        return;
      }
      if (result.action === 'yes') {
        this.store.dispatch(new WhitelistVoucherServiceAction({
          id: row.id,
          email: row.email,
          accepted: true,
        }));
      } else if (result.action === 'no') {
        this.store.dispatch(new WhitelistVoucherServiceAction({
          id: row.id,
          email: row.email,
          accepted: false,
        }));
      }
    });

  }

  private getServices() {
    this.store.dispatch(new GetServicesAction());
  }
}

function compare(a: string, b: string, isAsc: boolean) {
  return (a < b ? -1 : 1) * (isAsc ? 1 : -1);
}
