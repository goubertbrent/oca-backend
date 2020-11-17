import { forwardRef } from '@angular/core';
import { ControlValueAccessor, FormArray, NG_VALUE_ACCESSOR } from '@angular/forms';

export const COLOR_REGEXP = /^([a-f\d])([a-f\d])([a-f\d])$/i;

export function normalizeColorInput(input: string | null) {
  return input ? `#${input}` : input;
}

export function normalizeColorOutput(input: string | null) {
  return input ? input.replace('#', '')
    .replace(COLOR_REGEXP, (_: string, r: string, g: string, b: string) => r + r + g + g + b + b) : input;
}

/**
 * Use this class to be able to use [(ngModel)] on a custom component.
 * Access its value by using {{ value }} in templates.
 */
export abstract class AbstractControlValueAccessor implements ControlValueAccessor {
  onTouched: () => void;
  onChange: (_: any) => void;
  protected _value: any = null;

  get value(): any {
    return this._value;
  }

  set value(v: any) {
    if (v !== this._value) {
      this._value = v;
      this.onChange(v);
    }
  }

  writeValue(value: any): void {
    this.value = value;
  }

  registerOnChange(fn: (_: any) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }
}


export abstract class FileSelector {

  onFileSelected(file: File): void {
    throw new Error('onFileSelected is not implemented');
  }

  onMultiFilesSelected(files: FileList) {
    throw new Error('onMultiFilesSelected is not implemented');
  }

  onFilePicked(event: any) {
    // different browsers set the target
    // with different properties (target, srcElement)
    let element = event.srcElement;
    if (!element) {
      element = event.target;
    }

    if (element.files.length > 1) {
      this.onMultiFilesSelected(element.files);
    } else if (element.files.length) {
      this.onFileSelected(element.files[ 0 ]);
    }
  }

  /*
    data is a base64 encoded content of the file
  */
  onReadCompleted(data: string) {
    throw new Error('onReadCompleted is not implemented');
  }

  onMaxSizeReached() {
    throw new Error('onMaxSizeReached is not implemented');
  }

  readFile(file: File, maxSize?: number) {
    const reader = new FileReader();
    let aborted: boolean;

    if (maxSize) {
      reader.onprogress = (e: ProgressEvent) => {
        if (e.lengthComputable && e.loaded > maxSize) {
          this.onMaxSizeReached();
          aborted = true;
          reader.abort();
        }
      };
    }

    reader.onloadend = (e: ProgressEvent) => {
      if (reader.result && !aborted) {
        // Get rid of data:application/zip;base64,
        const result = isArrayBuffer(reader.result) ? arrayBufferToString(reader.result) : reader.result;
        this.onReadCompleted(result.split(',')[ 1 ]);
      }
    };
    reader.readAsDataURL(file);
  }
}

export abstract class ImageSelector extends FileSelector {

  abstract onImageValidated(isValid: boolean, data?: string | null): void;

  validateImage(file: File, width: number, height: number) {
    this.validateImagWithCompareFunc(file, (w: number, h: number) => width === w && height === h);
  }

  validateImageByRatio(file: File, ratio: number) {
    this.validateImagWithCompareFunc(file, (w: number, h: number) => ratio === w / h);
  }

  private validateImagWithCompareFunc(file: File, compareFunc: (w: number, h: number) => boolean) {
    const self = this;
    const reader = new FileReader();
    reader.addEventListener('load', () => {
      const image = new Image();
      const imageUrl = getFileReaderResult(reader);
      image.addEventListener('load', () => {
        if (compareFunc(image.width, image.height)) {
          self.onImageValidated(true, imageUrl.split(',')[ 1 ]);
        } else {
          self.onImageValidated(false);
        }
      });
      image.src = imageUrl;
    });
    reader.readAsDataURL(file);
  }

}


export function makeNgModelProvider(component: any) {
  return {
    provide: NG_VALUE_ACCESSOR,
    useExisting: forwardRef(() => component),
    multi: true,
  };
}

export function getFileReaderResult(reader: FileReader) {
  return isArrayBuffer(reader.result) ? arrayBufferToString(reader.result) : reader.result as string;
}

function isArrayBuffer(value: string | ArrayBuffer | null): value is ArrayBuffer {
  return typeof ArrayBuffer === 'function' && (value instanceof ArrayBuffer || toString.call(value) === '[object ArrayBuffer]');
}

function arrayBufferToString(buf: ArrayBuffer) {
  // http://stackoverflow.com/a/11058858
  return String.fromCharCode.apply(null, new Uint16Array(buf) as any);
}

export function cloneDeep<T>(object: T) {
  return JSON.parse(JSON.stringify(object)) as T;
}

/**
 * Moves an item in a FormArray to another position.
 * @param formArray FormArray instance in which to move the item.
 * @param fromIndex Starting index of the item.
 * @param toIndex Index to which he item should be moved.
 */
export function moveItemInFormArray(formArray: FormArray, fromIndex: number, toIndex: number): void {
  if (fromIndex === toIndex) {
    return;
  }

  const delta = toIndex > fromIndex ? 1 : -1;
  for (let i = fromIndex; i * delta < toIndex * delta; i += delta) {
    const previous = formArray.at(i);
    const current = formArray.at(i + delta);
    formArray.setControl(i, current);
    formArray.setControl(i + delta, previous);
  }
}
