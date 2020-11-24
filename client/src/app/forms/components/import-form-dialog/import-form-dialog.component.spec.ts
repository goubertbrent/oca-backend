import { ComponentFixture, TestBed, waitForAsync } from '@angular/core/testing';

import { ImportFormDialogComponent } from './import-form-dialog.component';

describe('ImportFormDialogComponent', () => {
  let component: ImportFormDialogComponent;
  let fixture: ComponentFixture<ImportFormDialogComponent>;

  beforeEach(waitForAsync(() => {
    TestBed.configureTestingModule({
      declarations: [ ImportFormDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ImportFormDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
