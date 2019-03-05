import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { FormDetailsPageComponent } from './form-details-page.component';

describe('FormDetailsPageComponent', () => {
  let component: FormDetailsPageComponent;
  let fixture: ComponentFixture<FormDetailsPageComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ FormDetailsPageComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(FormDetailsPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
