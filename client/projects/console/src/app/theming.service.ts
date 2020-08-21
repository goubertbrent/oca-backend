import { ApplicationRef, Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

type SupportedThemes = 'dark-theme' | 'light-theme';

@Injectable({ providedIn: 'root' })
export class ThemingService {
  themes: SupportedThemes[] = ['dark-theme', 'light-theme'];
  theme = new BehaviorSubject<SupportedThemes>('light-theme');

  constructor(private ref: ApplicationRef) {
    // Initially check if dark mode is enabled on system
    const darkModeOn = window.matchMedia('(prefers-color-scheme: dark)').matches ?? false;

    // If dark mode is enabled then directly switch to the dark-theme
    if (darkModeOn) {
      this.theme.next('dark-theme');
    }

    // Watch for changes of the preference
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    if (media.addEventListener === undefined) {
      // For safari
      media.addListener(event => this.toggleTheme(event.matches));
    } else {
      media.addEventListener('change', event => this.toggleTheme(event.matches), { passive: true });
    }
  }

  private toggleTheme(turnOn: boolean) {
    this.theme.next(turnOn ? 'dark-theme' : 'light-theme');
    // Trigger refresh of UI
    this.ref.tick();
  }
}
