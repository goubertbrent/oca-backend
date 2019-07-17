import { TestBed } from '@angular/core/testing';
import { TestingModule } from '../../../testing/testing.module';

import { ErrorService } from './error.service';

beforeEach(() => TestBed.configureTestingModule({ imports: [ TestingModule ] }));
describe('ErrorService', () => {

  it('should be created', () => {
    const service: ErrorService = TestBed.get(ErrorService);
    expect(service).toBeTruthy();
  });

  it('should return error messages', () => {
    const service: ErrorService = TestBed.get(ErrorService);
    expect(service.getErrorMessage({ error: 'teapot', data: null, status_code: 418 })).toBe('oca.error-occured-unknown-try-again');
    const msg = 'error message';
    expect(service.getErrorMessage({ error: 'oca.error', data: { message: msg }, status_code: 418 })).toBe(msg);
  });
});
