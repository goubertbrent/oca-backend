## Usage

Add it inside a mat-select

```angular2html
```angular2html
<mat-select [formControl]="selectControl" multiple>
  <oca-select-all-option [control]="selectControl"
                         text="Select all"
                         [values]="possibleValues"></oca-select-all-option>
  <mat-option *ngFor="let value of possibleValues" [value]="value">
    {{ value }}
  </mat-option>
</mat-select>
```
