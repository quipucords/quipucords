class SourcesApi {
  static getSources() {
    return fetch(process.env.REACT_APP_SOURCES_API).then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(response.statusText);
      }
    });
  }
}

export default SourcesApi;
