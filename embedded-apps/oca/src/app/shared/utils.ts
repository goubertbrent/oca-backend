export function downloadFile(fileName: string, contentType: string, content: string) {
  const element = document.createElement('a');
  element.setAttribute('href', content);
  element.setAttribute('download', fileName);
  element.style.display = 'none';
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}
