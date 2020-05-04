import { AbstractControl, FormArray, FormControl, FormGroup } from '@angular/forms';
import { Observable } from 'rxjs';

// From https://github.com/angular/angular/issues/13721#issuecomment-468745950

// I don't know why Angular Team doesn't define it https://github.com/angular/angular/blob/9.0.0/packages/forms/src/model.ts#L15-L45
type STATUS = 'VALID' | 'INVALID' | 'PENDING' | 'DISABLED';
//string is added only becouse Angular base class use string insted of union type https://github.com/angular/angular/blob/9.0.0/packages/forms/src/model.ts#L196)
type STATUSs = STATUS | string;

// OVVERRIDE TYPES WITH STRICT TYPED INTERFACES + SOME TYPE TRICKS TO COMPOSE INTERFACE (https://github.com/Microsoft/TypeScript/issues/16936)
export interface AbstractControlTyped<T> extends AbstractControl {
  // BASE PROPS AND METHODS COMMON TO ALL FormControl/FormGroup/FormArray
  readonly value: T;
  valueChanges: Observable<T>;
  readonly status: STATUSs;
  statusChanges: Observable<STATUS>;

  get<V = unknown>(path: Array<string | number> | string): AbstractControlTyped<V> | null;

  setValue<V>(value: V extends T ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;

  patchValue<V>(value: V extends Partial<T> ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;

  reset<V>(value?: V extends Partial<T> ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;
}

export interface FormControlTyped<T> extends FormControl {
  // COPIED FROM AbstractControlTyped<T> BECOUSE TS NOT SUPPORT MULPILE extends FormControl, AbstractControlTyped<T>
  readonly value: T;
  valueChanges: Observable<T>;
  readonly status: STATUSs;
  statusChanges: Observable<STATUS>;

  get<V = unknown>(path: Array<string | number> | string): AbstractControlTyped<V> | null;

  setValue<V>(value: V extends T ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;

  patchValue<V>(value: V extends Partial<T> ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;

  reset<V>(value?: V extends Partial<T> ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;
}

type SimpleType = string | number | Date | null;
type SimpleTypes = SimpleType | SimpleTypes[];

export type Controls<T> = { [P in keyof T]: T[P] extends SimpleTypes ? AbstractControlTyped<T[P]> : FormGroupTyped<T[P]> };

export interface FormGroupTyped<T> extends FormGroup {
  controls: Controls<T>;
  readonly value: T;
  valueChanges: Observable<T>;
  readonly status: STATUSs;
  statusChanges: Observable<STATUS>;

  registerControl<P extends keyof T>(name: P, control: AbstractControlTyped<T[P]>): AbstractControlTyped<T[P]>;

  registerControl<V = any>(name: string, control: AbstractControlTyped<V>): AbstractControlTyped<V>;

  addControl<P extends keyof T>(name: P, control: AbstractControlTyped<T[P]>): void;

  addControl<V = any>(name: string, control: AbstractControlTyped<V>): void;

  removeControl(name: keyof T): void;

  removeControl(name: string): void;

  setControl<P extends keyof T>(name: P, control: AbstractControlTyped<T[P]>): void;

  setControl<V = any>(name: string, control: AbstractControlTyped<V>): void;

  contains(name: keyof T): boolean;

  contains(name: string): boolean;

  get<P extends keyof T>(path: P): AbstractControlTyped<T[P]>;

  get<V = unknown>(path: Array<string | number> | string): AbstractControlTyped<V> | null;

  getRawValue(): T & { [disabledProp in string | number]: any };

  setValue<V>(value: V extends T ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;

  patchValue<V>(value: V extends Partial<T> ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;

  reset<V>(value?: V extends Partial<T> ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;
}

export interface FormArrayTyped<T> extends FormArray {
  // PROPS AND METHODS SPECIFIC OF FormGroup
  controls: AbstractControlTyped<T>[];
  readonly value: T[];
  valueChanges: Observable<T[]>;
  readonly status: STATUSs;
  statusChanges: Observable<STATUS>;

  at(index: number): AbstractControlTyped<T>;

  push<V = T>(ctrl: AbstractControlTyped<V>): void;

  insert<V = T>(index: number, control: AbstractControlTyped<V>): void;

  setControl<V = T>(index: number, control: AbstractControlTyped<V>): void;

  getRawValue(): T[];

  get<V = unknown>(path: Array<string | number> | string): AbstractControlTyped<V> | null;

  setValue<V>(value: V extends T[] ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;

  patchValue<V>(value: V extends Partial<T>[] ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;

  reset<V>(value?: V extends Partial<T>[] ? V : never, options?: { onlySelf?: boolean; emitEvent?: boolean }): void;
}
