import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { UserAutoCompleteDialogComponent } from './user-auto-complete-dialog.component';

describe('UserAutoCompleteDialogComponent', () => {
  let component: UserAutoCompleteDialogComponent;
  let fixture: ComponentFixture<UserAutoCompleteDialogComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ UserAutoCompleteDialogComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(UserAutoCompleteDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
