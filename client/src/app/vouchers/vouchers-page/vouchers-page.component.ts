import { ChangeDetectionStrategy, Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatSlideToggleChange } from '@angular/material/slide-toggle';
import { MatSort } from '@angular/material/sort';
import { MatTableDataSource } from '@angular/material/table';
import { select, Store } from '@ngrx/store';
import { Observable, Subject } from 'rxjs';
import { take, takeUntil } from 'rxjs/operators';
import { VoucherProviderId, VoucherService, VouchersServiceList } from '../vouchers';
import { ExportVoucherServicesAction, GetServicesAction, SaveVoucherSettingsAction } from '../vouchers.actions';
import { getVoucherList, getVoucherServices, voucherServicesLoading } from '../vouchers.selectors';

@Component({
  selector: 'oca-vouchers-page',
  templateUrl: './vouchers-page.component.html',
  styleUrls: ['./vouchers-page.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VouchersPageComponent implements OnInit, OnDestroy {
  @ViewChild(MatPaginator, { static: true }) paginator: MatPaginator;
  @ViewChild(MatSort, { static: true }) sort: MatSort;

  cirklo = VoucherProviderId.CIRKLO;
  selectedOrganizationType = 1;
  organizationTypes = [
    { type: 1, label: 'oca.associations' },
    { type: 2, label: 'oca.merchants' },
    { type: 3, label: 'oca.community_services' },
    { type: 4, label: 'oca.care' },
  ];
  displayedColumns = ['name', 'creation_time', 'enabled'];
  pageIndex = 0;
  pageSize = 50;
  loading$: Observable<boolean>;
  voucherList$: Observable<VouchersServiceList>;
  dataSource = new MatTableDataSource<VoucherService>();

  private destroyed$ = new Subject();

  constructor(private store: Store<any>) {
  }

  ngOnInit(): void {
    this.dataSource.paginator = this.paginator;
    this.dataSource.sort = this.sort;
    this.getServices();
    this.store.pipe(select(getVoucherServices), takeUntil(this.destroyed$)).subscribe(services => {
      this.dataSource.data = services;
    });
    this.voucherList$ = this.store.pipe(select(getVoucherList));
    this.loading$ = this.store.pipe(select(voucherServicesLoading));
  }

  ngOnDestroy() {
    this.destroyed$.next();
    this.destroyed$.complete();
  }

  tabChanged(index: number) {
    const selected = this.organizationTypes[ index ];
    this.selectedOrganizationType = selected.type;
    this.getServices();
  }

  toggleProvider($event: MatSlideToggleChange, service: VoucherService, provider: VoucherProviderId) {
    let providers: VoucherProviderId[];
    if ($event.checked) {
      providers = [...service.providers, provider];
    } else {
      providers = service.providers.filter(p => p !== provider);
    }
    this.store.dispatch(new SaveVoucherSettingsAction({
      serviceEmail: service.service_email,
      providers,
    }));
  }

  pageChanged($event: PageEvent) {
    if ($event.pageSize === this.pageSize) {
      // Previous does nothing, next loads the next page
      this.pageIndex = $event.pageIndex;
      if (($event.previousPageIndex as number) < $event.pageIndex) {
        this.voucherList$.pipe(take(1)).subscribe(({ cursor, more }) => {
          if (more) {
            this.store.dispatch(new GetServicesAction({
              organizationType: this.selectedOrganizationType,
              cursor,
              sort: this.sort.active,
              pageSize: this.pageSize,
            }));
          }
        });
      }
    } else {
      this.pageIndex = 0;
      this.pageSize = $event.pageSize;
      this.getServices();
    }
  }

  export() {
    this.store.dispatch(new ExportVoucherServicesAction());
  }

  onSorted() {
    this.getServices();
  }

  private getServices() {
    if (this.sort.active === 'name') {
      this.sort.direction = 'asc';
    } else {
      this.sort.direction = 'desc';
    }
    this.store.dispatch(new GetServicesAction({
      organizationType: this.selectedOrganizationType,
      cursor: null,
      pageSize: this.pageSize,
      sort: this.sort.active,
    }));
  }
}
