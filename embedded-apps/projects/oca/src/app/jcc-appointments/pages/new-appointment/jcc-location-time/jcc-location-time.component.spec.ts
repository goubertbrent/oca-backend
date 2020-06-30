import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { JccLocationTimeComponent } from './jcc-location-time.component';

describe('JccLocationTimeComponent', () => {
  let component: JccLocationTimeComponent;
  let fixture: ComponentFixture<JccLocationTimeComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [JccLocationTimeComponent],
      schemas: [CUSTOM_ELEMENTS_SCHEMA],
    })
      .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(JccLocationTimeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
