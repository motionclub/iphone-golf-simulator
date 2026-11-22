for (const preview of document.querySelectorAll("[data-preview-of]")) {
  const artwork = document.getElementById(preview.dataset.previewOf);
  const thumbnail = artwork.cloneNode(true);
  thumbnail.removeAttribute("id");
  preview.append(thumbnail);
}
