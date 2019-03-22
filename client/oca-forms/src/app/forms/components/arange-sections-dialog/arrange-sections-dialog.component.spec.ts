import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ArrangeSectionsDialogComponent } from './arrange-sections-dialog.component';

describe('ArangeSectionsComponent', () => {
  let component: ArrangeSectionsDialogComponent;
  let fixture: ComponentFixture<ArrangeSectionsDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ArrangeSectionsDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ArrangeSectionsDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
