const BASE_PATH = '/ui';

$(function () {
  $('#header').load(`${BASE_PATH}/partials/header.html`);
  $('#footer').load(`${BASE_PATH}/partials/footer.html`);
  $('#sidebar').load(`${BASE_PATH}/partials/sidebar.html`, function () {
    const page = window.location.pathname.split('/').pop();
    $(`#sidebar a[href='${page}']`).addClass('active');
  });
});

function resolveApiKey() {
  const metaKey = document.querySelector("meta[name='api-key']");
  if (metaKey && metaKey.content) {
    return metaKey.content;
  }
  const metaEndpoint = document.querySelector("meta[name='api-key-endpoint']");
  if (metaEndpoint && metaEndpoint.content) {
    try {
      const xhr = new XMLHttpRequest();
      xhr.open('GET', metaEndpoint.content, false);
      xhr.send(null);
      if (xhr.status === 200 && xhr.responseText.trim()) {
        return xhr.responseText.trim();
      }
    } catch (err) {
      console.error('Failed to fetch API key', err);
    }
  }
  return 'secret';
}

window.API_HEADERS = { 'X-API-Key': resolveApiKey() };

window.api = {
  get: (path) =>
    $.ajax({ url: path, headers: API_HEADERS, dataType: 'json' }),
  post: (path, data) =>
    $.ajax({
      url: path,
      method: 'POST',
      headers: API_HEADERS,
      contentType: 'application/json',
      data: JSON.stringify(data),
      dataType: 'json',
    }),
  delete: (path) =>
    $.ajax({ url: path, method: 'DELETE', headers: API_HEADERS }),
};
