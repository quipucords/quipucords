class SourcesApi {
  static getSources() {
    return fetch('http://localhost:4000/api/v1/sources/').then(response => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error(response.statusText);
      }
    });
  }
}

export default SourcesApi;
