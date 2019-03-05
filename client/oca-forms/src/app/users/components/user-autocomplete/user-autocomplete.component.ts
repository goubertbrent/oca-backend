import { ChangeDetectionStrategy, Component, EventEmitter, OnInit, Output } from '@angular/core';
import { FormControl, FormGroup } from '@angular/forms';
import { MatAutocompleteSelectedEvent } from '@angular/material';
import { Observable } from 'rxjs';
import { debounceTime, switchMap } from 'rxjs/operators';
import { UserDetailsTO } from '../../interfaces';
import { UsersService } from '../../users.service';

@Component({
  selector: 'oca-user-autocomplete',
  templateUrl: './user-autocomplete.component.html',
  styleUrls: [ './user-autocomplete.component.scss' ],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UserAutocompleteComponent implements OnInit {
  results$: Observable<UserDetailsTO[]>;
  formGroup: FormGroup;
  formControl: FormControl;
  @Output() optionSelected = new EventEmitter<UserDetailsTO>();

  constructor(private usersService: UsersService) {
  }

  ngOnInit() {
    this.formControl = new FormControl();
    this.formGroup = new FormGroup({ input: this.formControl });
    this.results$ = this.formControl.valueChanges.pipe(
      debounceTime(500),
      switchMap(value => this.usersService.searchUsers(value)),
    );
  }

  onOptionSelected(event: MatAutocompleteSelectedEvent) {
    this.optionSelected.emit(event.option.value);
  }

  displayWith(value?: UserDetailsTO) {
    if (value) {
      return value.email;
    }
  }
}
