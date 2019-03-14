import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FormListPageComponent } from './form-list-page.component';

describe('FormListPageComponent', () => {
  let component: FormListPageComponent;
  let fixture: ComponentFixture<FormListPageComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FormListPageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FormListPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
